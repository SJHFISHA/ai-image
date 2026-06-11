"""
模型价格配置相关路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.model_price import (
    ModelPriceConfigResponse,
    ModelPriceConfigListResponse
)
from app.schemas.common import ApiResponse
from app.services import model_price_service

router = APIRouter(prefix="/model-prices", tags=["模型价格"])


@router.get("", response_model=ApiResponse[ModelPriceConfigListResponse], summary="查询模型价格配置")
def get_model_prices(
    capability_type: Optional[str] = Query(None, description="能力类型: image, video, text, audio"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    查询模型价格配置列表

    - capability_type: 能力类型筛选（可选，不传则返回所有类型）

    需要在请求头中携带: Authorization: Bearer <token>
    """
    configs = model_price_service.get_model_price_configs(
        db=db,
        capability_type=capability_type,
        enabled_only=True
    )

    items = [
        ModelPriceConfigResponse(
            id=config.id,
            model_key=config.model_config.model_key,
            model_name=config.model_config.model_name,
            provider_key=config.model_config.provider_key,
            capability_type=config.model_config.capability_type,
            image_size=config.image_size,
            image_count=config.image_count,
            video_duration=config.video_duration,
            video_resolution=config.video_resolution,
            points=config.points
        )
        for config in configs
    ]

    response_data = ModelPriceConfigListResponse(
        total=len(items),
        items=items
    )

    return ApiResponse(
        code=0,
        message="success",
        data=response_data,
        success=True
    )
