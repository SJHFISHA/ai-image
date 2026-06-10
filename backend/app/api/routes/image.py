"""
生图相关路由
"""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.generation import (
    ImageGenerateRequest,
    TaskCreateResponse
)
from app.schemas.common import ApiResponse
from app.services import generation_service, conversation_service
from app.utils.logger import app_logger

router = APIRouter(prefix="/image", tags=["生图"])

def normalize_image_value(value: str) -> str:
    """
    统一图片返回格式。
    URL 直接返回，base64 自动补 data:image/png;base64, 前缀，方便前端 img 直接显示。
    """
    if value.startswith("http://") or value.startswith("https://"):
        return value

    if value.startswith("data:image/"):
        return value

    return f"data:image/png;base64,{value}"


def extract_images_from_api_result(api_result) -> list[str]:
    """
    从 API 中转站返回结果中提取图片 URL 或 base64。
    兼容 data 列表、data 对象、顶层 b64_json、顶层 images、纯字符串等格式。
    """
    images = []

    if isinstance(api_result, str):
        images.append(normalize_image_value(api_result))
        return images

    if not isinstance(api_result, dict):
        return images

    data = api_result.get("data")

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                for key in ("url", "b64_json", "image_url", "image"):
                    value = item.get(key)
                    if value:
                        images.append(normalize_image_value(value))
                        break
            elif isinstance(item, str):
                images.append(normalize_image_value(item))

    elif isinstance(data, dict):
        for key in ("url", "b64_json", "image_url", "image"):
            value = data.get(key)
            if value:
                images.append(normalize_image_value(value))

        data_images = data.get("images")
        if isinstance(data_images, list):
            images.extend([
                normalize_image_value(item)
                for item in data_images
                if isinstance(item, str)
            ])

    for key in ("url", "b64_json", "image_url", "image"):
        value = api_result.get(key)
        if value:
            images.append(normalize_image_value(value))

    top_images = api_result.get("images")
    if isinstance(top_images, list):
        images.extend([
            normalize_image_value(item)
            for item in top_images
            if isinstance(item, str)
        ])

    return images


@router.post("/generate", response_model=ApiResponse[TaskCreateResponse], summary="创建生图任务")
def create_image_task(
    request: ImageGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建生图任务（异步执行）

    - session_id: 可选会话ID，不传则自动创建新会话
    - price_config_id: 模型价格配置ID（从 /api/model-prices 获取）
    - prompt: 提示词

    流程：
    1. 获取或创建会话
    2. 写入用户消息
    3. 创建任务 + 冻结积分（同一事务）
    4. 写入 assistant 消息（running）
    5. 立即返回 task_id 和 running 状态
    6. 后台异步执行生图 + 写历史

    需要在请求头中携带: Authorization: Bearer <token>
    """
    # 1. 获取或创建会话
    conversation, session_is_new = conversation_service.get_or_create_session(
        db=db,
        user_id=current_user.id,
        session_id=request.session_id,
        session_type="image",
        title=request.prompt[:50] if request.prompt else None,
    )

    # 2. 写入用户消息
    user_message = conversation_service.create_message(
        db=db,
        session_id=conversation.session_id,
        user_id=current_user.id,
        role="user",
        content_type="text",
        content_text=request.prompt,
    )

    # 3. 创建任务（冻结积分 + 创建任务在同一事务）
    #    如果失败需要回滚本次新建的会话和消息
    try:
        task = generation_service.create_image_task(
            db=db,
            user_id=current_user.id,
            price_config_id=request.price_config_id,
            prompt=request.prompt
        )
    except Exception as e:
        # 回滚用户消息
        try:
            db.delete(user_message)
            # 只有本次新建的会话才删除，避免误删已有空会话
            if session_is_new:
                db.delete(conversation)
            db.commit()
        except Exception:
            db.rollback()
        raise

    # 4. 写入 assistant 消息（running）
    assistant_message = conversation_service.create_message(
        db=db,
        session_id=conversation.session_id,
        user_id=current_user.id,
        role="assistant",
        content_type="image",
        content_text=None,
        task_id=task.task_id,
        status_val="running",
    )

    # 5. 更新会话预览
    conversation_service.update_session_preview(
        db=db,
        session_id=conversation.session_id,
        preview=f"生成图片: {request.prompt[:100]}",
    )

    # 6. 提交异步生图任务（传入会话和消息信息供后续写历史）
    background_tasks.add_task(
        generation_service.execute_image_generation_by_task_id,
        task.task_id,
        request.prompt,
        session_id=conversation.session_id,
        assistant_message_id=assistant_message.message_id,
    )

    # 立即返回，不等待生图完成
    return ApiResponse(
        code=0,
        message="任务已提交",
        data=TaskCreateResponse(
            task_id=task.task_id,
            status="running",
            frozen_points=task.frozen_points,
            error_message=None,
            session_id=conversation.session_id,
        ),
        success=True
    )
