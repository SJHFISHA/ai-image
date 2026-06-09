"""
生图相关路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.generation import (
    ImageGenerateRequest,
    TaskCreateResponse
)
from app.services import generation_service
from app.providers.api_gateway_provider import api_gateway_provider
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


@router.post("/generate", response_model=TaskCreateResponse, summary="创建生图任务")
def create_image_task(
    request: ImageGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建生图任务

    - price_config_id: 模型价格配置ID（从 /api/model-prices 获取）
    - prompt: 提示词

    流程：
    1. 根据 price_config_id 查询模型配置
    2. 检查积分是否足够
    3. 冻结积分
    4. 创建任务
    5. 调用模型生成图片
    6. 成功后扣除冻结积分，失败后退回冻结积分

    需要在请求头中携带: Authorization: Bearer <token>
    """
    task = generation_service.create_image_task(
        db=db,
        user_id=current_user.id,
        price_config_id=request.price_config_id,
        prompt=request.prompt
    )

    # 调用真实 API 中转站
    try:
        app_logger.info(f"开始调用API生图: task_id={task.task_id}")

        # 更新任务状态为运行中
        task.status = "running"
        db.commit()

        # 调用 API 中转站
        api_result = api_gateway_provider.generate_image(
            model=task.model_key,
            prompt=request.prompt,
            size=task.image_size or "1024x1024",
            count=task.image_count or 1,
            quality="low",
            format="jpeg"
        )

        # 解析返回结果，提取图片 URL 或 base64
        images = extract_images_from_api_result(api_result)

        if not images:
            raise Exception(f"API未返回图片数据，原始返回: {api_result}")

        # 构建结果
        result = {"images": images}

        # 成功结算
        generation_service.settle_task_success(db, task.task_id, result)
        task.status = "success"

        app_logger.info(f"生图成功: task_id={task.task_id}, images={len(images)}")

    except Exception as e:
        # 失败结算，退回积分
        error_msg = str(e)
        app_logger.error(f"生图失败: task_id={task.task_id}, error={error_msg}")
        generation_service.settle_task_failed(db, task.task_id, error_msg)
        task.status = "failed"

    return TaskCreateResponse(
        task_id=task.task_id,
        status=task.status,
        frozen_points=task.frozen_points
    )
