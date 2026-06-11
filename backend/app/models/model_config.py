"""
模型配置ORM模型
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, DateTime, Integer, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.utils.timezone import now_beijing_naive


class ModelConfig(Base):
    """模型配置表"""

    __tablename__ = "model_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    model_key: Mapped[str] = mapped_column(String(128), comment="真实模型标识")
    model_name: Mapped[str] = mapped_column(String(128), comment="前端展示名称")
    provider_key: Mapped[str] = mapped_column(String(64), comment="供应商标识")
    route_mode: Mapped[Optional[str]] = mapped_column(String(32), comment="路由模式: price, speed, success_rate")
    capability_type: Mapped[str] = mapped_column(String(32), comment="能力类型")

    enabled: Mapped[int] = mapped_column(SmallInteger, default=1, comment="是否启用")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    remark: Mapped[Optional[str]] = mapped_column(String(255), comment="备注")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_beijing_naive, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=now_beijing_naive,
        onupdate=now_beijing_naive,
        comment="更新时间",
    )

    price_configs: Mapped[List["ModelPriceConfig"]] = relationship(
        "ModelPriceConfig",
        back_populates="model_config",
        lazy="select"
    )

    def __repr__(self):
        return f"<ModelConfig(id={self.id}, model={self.model_key}, provider={self.provider_key})>"
