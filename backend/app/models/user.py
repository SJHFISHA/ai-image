"""
用户表ORM模型
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """用户表"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    username: Mapped[Optional[str]] = mapped_column(String(64), unique=True, comment="用户名")
    email: Mapped[Optional[str]] = mapped_column(String(128), unique=True, comment="邮箱")
    phone: Mapped[Optional[str]] = mapped_column(String(32), unique=True, comment="手机号")

    password_hash: Mapped[str] = mapped_column(String(255), comment="密码哈希")

    nickname: Mapped[Optional[str]] = mapped_column(String(64), comment="昵称")
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255), comment="头像URL")

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

    # 关联关系
    point_account: Mapped[Optional["UserPointAccount"]] = relationship(
        "UserPointAccount",
        back_populates="user",
        uselist=False
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"
