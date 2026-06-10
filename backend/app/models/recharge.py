"""
充值套餐和充值订单ORM模型
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, BigInteger, Numeric, DateTime, SmallInteger, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.utils.timezone import now_beijing_naive


class RechargePackage(Base):
    """充值套餐表"""

    __tablename__ = "recharge_packages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    package_name: Mapped[str] = mapped_column(String(64), comment="套餐名称")

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), comment="充值金额")
    base_points: Mapped[int] = mapped_column(BigInteger, comment="基础积分")
    bonus_points: Mapped[int] = mapped_column(BigInteger, default=0, comment="赠送积分")
    total_points: Mapped[int] = mapped_column(BigInteger, comment="总积分")

    enabled: Mapped[int] = mapped_column(SmallInteger, default=1, comment="是否启用: 1=启用, 0=禁用")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_beijing_naive, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=now_beijing_naive,
        onupdate=now_beijing_naive,
        comment="更新时间"
    )

    def __repr__(self):
        return f"<RechargePackage(id={self.id}, name={self.package_name}, amount={self.amount})>"


class RechargeOrder(Base):
    """充值订单表"""

    __tablename__ = "recharge_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    order_no: Mapped[str] = mapped_column(String(64), unique=True, comment="充值订单号")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")

    package_id: Mapped[int] = mapped_column(BigInteger, comment="充值套餐ID")
    package_name: Mapped[str] = mapped_column(String(64), comment="套餐名称")

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), comment="支付金额")
    currency: Mapped[str] = mapped_column(String(16), default="CNY", comment="货币类型")

    base_points: Mapped[int] = mapped_column(BigInteger, comment="基础积分")
    bonus_points: Mapped[int] = mapped_column(BigInteger, default=0, comment="赠送积分")
    total_points: Mapped[int] = mapped_column(BigInteger, comment="总到账积分")

    pay_channel: Mapped[Optional[str]] = mapped_column(String(32), comment="支付渠道: alipay, wechat, stripe")
    pay_status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        comment="支付状态: pending, paid, failed, closed, refunded"
    )

    pay_trade_no: Mapped[Optional[str]] = mapped_column(String(128), comment="第三方支付流水号")

    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="支付成功时间")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_beijing_naive, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=now_beijing_naive,
        onupdate=now_beijing_naive,
        comment="更新时间"
    )

    def __repr__(self):
        return f"<RechargeOrder(order_no={self.order_no}, status={self.pay_status})>"
