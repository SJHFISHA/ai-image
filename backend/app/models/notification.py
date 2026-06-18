"""
系统通知 ORM 模型
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.utils.timezone import now_beijing_naive


class SystemNotification(Base):
    """系统通知表"""

    __tablename__ = "system_notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    notification_id: Mapped[str] = mapped_column(String(64), unique=True, comment="通知业务ID")

    title: Mapped[str] = mapped_column(String(128), comment="通知标题")
    content: Mapped[str] = mapped_column(Text, comment="通知内容")

    type: Mapped[str] = mapped_column(String(32), default="system", comment="通知类型")
    level: Mapped[str] = mapped_column(String(32), default="info", comment="通知等级")
    status: Mapped[str] = mapped_column(String(32), default="draft", comment="draft,published,disabled")
    target_type: Mapped[str] = mapped_column(String(32), default="all", comment="目标类型")

    publish_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="发布时间")
    expire_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="过期时间")
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, comment="创建管理员ID")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_beijing_naive, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=now_beijing_naive,
        onupdate=now_beijing_naive,
        comment="更新时间"
    )

    __table_args__ = (
        Index("idx_notification_status_time", "status", "publish_at", "expire_at"),
        Index("idx_notification_created_at", "created_at"),
    )


class UserNotificationRead(Base):
    """用户通知已读表"""

    __tablename__ = "user_notification_reads"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")
    notification_id: Mapped[str] = mapped_column(String(64), comment="通知业务ID")
    read_at: Mapped[datetime] = mapped_column(DateTime, default=now_beijing_naive, comment="已读时间")

    __table_args__ = (
        UniqueConstraint("user_id", "notification_id", name="uk_user_notification_read"),
        Index("idx_user_read", "user_id", "read_at"),
    )