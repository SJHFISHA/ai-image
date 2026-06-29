"""
邀请记录表ORM模型
"""
from datetime import datetime

from sqlalchemy import String, DateTime, BigInteger, SmallInteger, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.utils.timezone import now_beijing_naive


class InvitationRecord(Base):
    """邀请记录表"""

    __tablename__ = "invitation_records"

    # 唯一约束：同一邀请人和被邀请人只能有一条记录
    __table_args__ = (
        UniqueConstraint('inviter_user_id', 'invitee_user_id', name='uk_inviter_invitee'),
        Index('idx_inviter_user_id', 'inviter_user_id'),
        Index('idx_invitee_user_id', 'invitee_user_id'),
        Index('idx_invite_code', 'invite_code'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    inviter_user_id: Mapped[int] = mapped_column(BigInteger, comment="邀请人用户ID")
    invitee_user_id: Mapped[int] = mapped_column(BigInteger, comment="填写邀请码的用户ID")
    invite_code: Mapped[str] = mapped_column(String(16), comment="填写时使用的邀请码")

    reward_points: Mapped[int] = mapped_column(BigInteger, default=50, comment="双方奖励积分")
    reward_granted: Mapped[int] = mapped_column(SmallInteger, default=1, comment="是否已发放奖励: 1=已发放, 0=未发放")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_beijing_naive, comment="创建时间")

    def __repr__(self):
        return f"<InvitationRecord(id={self.id}, inviter={self.inviter_user_id}, invitee={self.invitee_user_id})>"
