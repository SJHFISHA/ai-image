"""
会话和消息ORM模型
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, BigInteger, DateTime, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.utils.timezone import now_beijing_naive


class ConversationSession(Base):
    """会话表"""

    __tablename__ = "conversation_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), unique=True, comment="会话ID")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")

    title: Mapped[Optional[str]] = mapped_column(String(255), comment="会话标题")
    session_type: Mapped[str] = mapped_column(
        String(32), default="mixed", comment="chat,image,video,mixed"
    )

    last_message_preview: Mapped[Optional[str]] = mapped_column(
        String(500), comment="最后一条消息预览"
    )
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, comment="最后消息时间"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_beijing_naive, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=now_beijing_naive,
        onupdate=now_beijing_naive,
        comment="更新时间"
    )

    def __repr__(self):
        return f"<ConversationSession(session_id={self.session_id}, title={self.title})>"


class ConversationMessage(Base):
    """会话消息表"""

    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String(64), unique=True, comment="消息ID")
    session_id: Mapped[str] = mapped_column(String(64), comment="会话ID")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")

    role: Mapped[str] = mapped_column(
        String(32), comment="user, assistant, system"
    )
    content_type: Mapped[str] = mapped_column(
        String(32), comment="text,image,video,mixed"
    )
    content_text: Mapped[Optional[str]] = mapped_column(Text, comment="文本内容或提示词")

    task_id: Mapped[Optional[str]] = mapped_column(
        String(64), comment="关联 generation_tasks.task_id"
    )
    status: Mapped[str] = mapped_column(
        String(32), default="success", comment="pending,running,success,failed"
    )

    metadata_json: Mapped[Optional[dict]] = mapped_column(
        JSON, comment="模型、尺寸、时长、积分等扩展信息"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_beijing_naive, comment="创建时间"
    )

    def __repr__(self):
        return f"<ConversationMessage(message_id={self.message_id}, role={self.role})>"


class MediaAsset(Base):
    """媒体资源表"""

    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    asset_id: Mapped[str] = mapped_column(String(64), unique=True, comment="资源ID")

    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")
    session_id: Mapped[Optional[str]] = mapped_column(String(64), comment="会话ID")
    message_id: Mapped[Optional[str]] = mapped_column(String(64), comment="消息ID")
    task_id: Mapped[Optional[str]] = mapped_column(String(64), comment="关联任务ID")

    media_type: Mapped[str] = mapped_column(
        String(32), comment="image,video,audio,file"
    )
    provider: Mapped[str] = mapped_column(
        String(32), default="qiniu", comment="qiniu,local,s3"
    )
    bucket: Mapped[Optional[str]] = mapped_column(String(128), comment="存储桶")
    object_key: Mapped[Optional[str]] = mapped_column(String(512), comment="云端对象key")
    url: Mapped[str] = mapped_column(String(1024), comment="公开访问URL")

    mime_type: Mapped[Optional[str]] = mapped_column(String(128), comment="MIME类型")
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, comment="文件大小")
    width: Mapped[Optional[int]] = mapped_column(comment="宽度")
    height: Mapped[Optional[int]] = mapped_column(comment="高度")
    duration_seconds: Mapped[Optional[int]] = mapped_column(comment="时长秒")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_beijing_naive, comment="创建时间"
    )

    def __repr__(self):
        return f"<MediaAsset(asset_id={self.asset_id}, type={self.media_type})>"
