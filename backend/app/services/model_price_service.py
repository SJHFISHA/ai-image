"""
模型价格配置业务逻辑模块
"""
from typing import Optional, List

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.model_price import ModelPriceConfig
from app.utils.logger import app_logger


def get_model_price_configs(
    db: Session,
    capability_type: Optional[str] = None,
    enabled_only: bool = True
) -> List[ModelPriceConfig]:
    """
    查询模型价格配置列表

    Args:
        db: 数据库Session
        capability_type: 能力类型筛选 (image, video, text, audio)
        enabled_only: 是否只查询启用的配置

    Returns:
        模型价格配置列表
    """
    query = db.query(ModelPriceConfig)

    if capability_type:
        query = query.filter(ModelPriceConfig.capability_type == capability_type)

    if enabled_only:
        query = query.filter(ModelPriceConfig.enabled == 1)

    configs = query.order_by(ModelPriceConfig.sort_order).all()

    return configs


def get_model_price_config_by_id(
    db: Session,
    config_id: int,
    capability_type: Optional[str] = None
) -> Optional[ModelPriceConfig]:
    """
    根据ID查询模型价格配置

    Args:
        db: 数据库Session
        config_id: 配置ID
        capability_type: 能力类型筛选

    Returns:
        模型价格配置对象，如果不存在返回None
    """
    query = db.query(ModelPriceConfig).filter(
        ModelPriceConfig.id == config_id,
        ModelPriceConfig.enabled == 1
    )

    if capability_type:
        query = query.filter(ModelPriceConfig.capability_type == capability_type)

    return query.first()


def validate_model_price_config(
    db: Session,
    price_config_id: int,
    capability_type: str = "image"
) -> ModelPriceConfig:
    """
    验证并获取模型价格配置

    Args:
        db: 数据库Session
        price_config_id: 价格配置ID
        capability_type: 能力类型

    Returns:
        模型价格配置对象

    Raises:
        HTTPException: 配置不存在或未启用时抛出异常
    """
    config = get_model_price_config_by_id(db, price_config_id, capability_type)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型价格配置不存在或未启用"
        )

    return config
