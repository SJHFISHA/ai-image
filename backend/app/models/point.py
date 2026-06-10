"""
积分账户和积分流水ORM模型
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, BigInteger, DateTime, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.utils.timezone import now_beijing_naive


class UserPointAccount(Base):
    """用户积分账户表"""

    __tablename__ = "user_point_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), unique=True, comment="用户ID")

    balance_points: Mapped[int] = mapped_column(BigInteger, default=0, comment="可用积分")
    frozen_points: Mapped[int] = mapped_column(BigInteger, default=0, comment="冻结积分")

    total_recharged_points: Mapped[int] = mapped_column(BigInteger, default=0, comment="累计充值积分")
    total_consumed_points: Mapped[int] = mapped_column(BigInteger, default=0, comment="累计消费积分")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_beijing_naive, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=now_beijing_naive,
        onupdate=now_beijing_naive,
        comment="更新时间"
    )

    # 关联关系
    user: Mapped["User"] = relationship("User", back_populates="point_account")

    def __repr__(self):
        return f"<UserPointAccount(user_id={self.user_id}, balance={self.balance_points})>"


class PointTransaction(Base):
    """积分流水表"""

    __tablename__ = "point_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    transaction_no: Mapped[str] = mapped_column(String(64), unique=True, comment="积分流水号")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")

    type: Mapped[str] = mapped_column(
        String(32),
        comment="类型: recharge, freeze, consume, refund, unfreeze, admin_adjust"
    )
    direction: Mapped[str] = mapped_column(
        String(16),
        comment="方向: income, expense, freeze, unfreeze"
    )

    points: Mapped[int] = mapped_column(BigInteger, comment="变动积分")

    balance_before: Mapped[int] = mapped_column(BigInteger, comment="变动前可用积分")
    balance_after: Mapped[int] = mapped_column(BigInteger, comment="变动后可用积分")

    frozen_before: Mapped[int] = mapped_column(BigInteger, default=0, comment="变动前冻结积分")
    frozen_after: Mapped[int] = mapped_column(BigInteger, default=0, comment="变动后冻结积分")

    related_order_no: Mapped[Optional[str]] = mapped_column(String(64), comment="关联充值订单号")
    related_task_id: Mapped[Optional[str]] = mapped_column(String(64), comment="关联生成任务ID")

    remark: Mapped[Optional[str]] = mapped_column(String(255), comment="备注")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_beijing_naive, comment="创建时间")

    def __repr__(self):
        return f"<PointTransaction(no={self.transaction_no}, type={self.type}, points={self.points})>"
