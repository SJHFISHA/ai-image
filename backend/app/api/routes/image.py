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
from app.schemas.common import ApiResponse
from app.services import generation_service
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
    # 创建任务
    task = generation_service.create_image_task(
        db=db,
        user_id=current_user.id,
        price_config_id=request.price_config_id,
        prompt=request.prompt
    )

    # 执行生图任务
    success, error_msg, result = generation_service.execute_image_generation(
        db=db,
        task=task,
        prompt=request.prompt
    )

    # 构建响应数据
    response_data = TaskCreateResponse(
        task_id=task.task_id,
        status=task.status,
        frozen_points=task.frozen_points,
        error_message=error_msg
    )

    return ApiResponse(
        code=0 if success else 50001,
        message="success" if success else error_msg,
        data=response_data,
        success=success
    )
