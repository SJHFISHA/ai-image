"""
后台管理员ORM模型
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AdminUser(Base):
    """后台管理员表"""

    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    username: Mapped[str] = mapped_column(String(64), unique=True, comment="管理员用户名")
    password_hash: Mapped[str] = mapped_column(String(255), comment="密码哈希")

    nickname: Mapped[Optional[str]] = mapped_column(String(64), comment="昵称")
    role: Mapped[str] = mapped_column(String(32), default="admin", comment="角色: admin, super_admin")

    status: Mapped[str] = mapped_column(String(32), default="normal", comment="状态: normal, disabled")

    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="最后登录时间")
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(64), comment="最后登录IP")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间"
    )

    def __repr__(self):
        return f"<AdminUser(id={self.id}, username={self.username})>"
