"""
模型价格配置ORM模型
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, BigInteger, Integer, DateTime, SmallInteger, Numeric, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.utils.timezone import now_beijing_naive


class ModelPriceConfig(Base):
    """模型价格配置表"""

    __tablename__ = "model_price_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    model_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("model_configs.id"),
        comment="关联 model_configs.id"
    )

    billing_mode: Mapped[str] = mapped_column(String(32), default="fixed", comment="计费方式: fixed")

    image_size: Mapped[Optional[str]] = mapped_column(String(32), comment="图片尺寸，例如 1024x1024")
    image_count: Mapped[int] = mapped_column(Integer, default=1, comment="生成图片数量")

    video_duration: Mapped[Optional[int]] = mapped_column(Integer, comment="视频时长，单位秒")
    video_resolution: Mapped[Optional[str]] = mapped_column(String(32), comment="视频分辨率")

    points: Mapped[int] = mapped_column(BigInteger, comment="用户消耗积分")

    cost_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 6), comment="预估真实成本，可选")
    cost_currency: Mapped[str] = mapped_column(String(16), default="CNY", comment="成本货币")

    enabled: Mapped[int] = mapped_column(SmallInteger, default=1, comment="是否启用: 1=启用, 0=禁用")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")

    remark: Mapped[Optional[str]] = mapped_column(String(255), comment="备注")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_beijing_naive, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=now_beijing_naive,
        onupdate=now_beijing_naive,
        comment="更新时间"
    )

    model_config: Mapped[Optional["ModelConfig"]] = relationship(
        "ModelConfig",
        back_populates="price_configs",
        lazy="select"
    )

    def __repr__(self):
        return f"<ModelPriceConfig(id={self.id}, model_id={self.model_id}, points={self.points})>"
