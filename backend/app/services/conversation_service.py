"""
会话业务逻辑模块
"""
from typing import Optional
from datetime import datetime
from app.utils.timezone import now_beijing_naive

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.conversation import (
    ConversationSession,
    ConversationMessage,
    MediaAsset,
)
from app.utils.id_generator import generate_task_id
from app.utils.logger import app_logger


def _generate_session_id() -> str:
    return generate_task_id("SESS")


def _generate_message_id() -> str:
    return generate_task_id("MSG")


def _generate_asset_id() -> str:
    return generate_task_id("AST")


# ======================== 会话操作 ========================

def create_session(
    db: Session,
    user_id: int,
    session_type: str = "mixed",
    title: Optional[str] = None,
) -> ConversationSession:
    """
    创建新会话

    Args:
        db: 数据库Session
        user_id: 用户ID
        session_type: 会话类型
        title: 会话标题

    Returns:
        创建的会话对象
    """
    session_id = _generate_session_id()

    conversation = ConversationSession(
        session_id=session_id,
        user_id=user_id,
        title=title or "新的创作",
        session_type=session_type,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    app_logger.info(f"创建会话: session_id={session_id}, user_id={user_id}")
    return conversation


def get_or_create_session(
    db: Session,
    user_id: int,
    session_id: Optional[str] = None,
    session_type: str = "image",
    title: Optional[str] = None,
) -> tuple:
    """
    获取或创建会话

    如果传了 session_id 且存在则返回已有会话，否则创建新会话。

    Returns:
        (ConversationSession, bool) - (会话对象, 是否本次新建)
    """
    if session_id:
        conversation = db.query(ConversationSession).filter(
            ConversationSession.session_id == session_id,
            ConversationSession.user_id == user_id,
        ).first()
        if conversation:
            return conversation, False

    return create_session(db, user_id, session_type, title), True


def get_user_sessions(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """
    查询用户会话列表

    Returns:
        {"total": int, "items": list}
    """
    query = db.query(ConversationSession).filter(
        ConversationSession.user_id == user_id,
    )

    total = query.count()
    sessions = query.order_by(
        ConversationSession.updated_at.desc()
    ).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {"total": total, "items": sessions}


def get_session_detail(
    db: Session,
    session_id: str,
    user_id: int,
) -> Optional[ConversationSession]:
    """
    获取会话详情（含消息列表）
    """
    return db.query(ConversationSession).filter(
        ConversationSession.session_id == session_id,
        ConversationSession.user_id == user_id,
    ).first()


def delete_session(db: Session, session_id: str, user_id: int) -> bool:
    """
    删除会话及其关联的消息和媒体资源
    """
    conversation = db.query(ConversationSession).filter(
        ConversationSession.session_id == session_id,
        ConversationSession.user_id == user_id,
    ).first()

    if not conversation:
        return False

    # 删除关联的媒体资源
    db.query(MediaAsset).filter(
        MediaAsset.session_id == session_id
    ).delete()

    # 删除关联的消息
    db.query(ConversationMessage).filter(
        ConversationMessage.session_id == session_id
    ).delete()

    # 删除会话本身
    db.delete(conversation)
    db.commit()

    app_logger.info(f"删除会话: session_id={session_id}")
    return True


def update_session_preview(
    db: Session,
    session_id: str,
    preview: str,
    title: Optional[str] = None,
):
    """
    更新会话最后消息预览和标题
    """
    conversation = db.query(ConversationSession).filter(
        ConversationSession.session_id == session_id
    ).first()

    if conversation:
        conversation.last_message_preview = preview[:500] if preview else None
        conversation.last_message_at = now_beijing_naive()
        if title:
            conversation.title = title
        db.commit()


# ======================== 消息操作 ========================

def create_message(
    db: Session,
    session_id: str,
    user_id: int,
    role: str,
    content_type: str,
    content_text: Optional[str] = None,
    task_id: Optional[str] = None,
    status_val: str = "success",
    metadata_json: Optional[dict] = None,
) -> ConversationMessage:
    """
    创建消息

    Args:
        db: 数据库Session
        session_id: 会话ID
        user_id: 用户ID
        role: 角色 (user, assistant, system)
        content_type: 内容类型 (text, image, video, mixed)
        content_text: 文本内容
        task_id: 关联任务ID
        status_val: 状态
        metadata_json: 扩展信息

    Returns:
        创建的消息对象
    """
    message_id = _generate_message_id()

    message = ConversationMessage(
        message_id=message_id,
        session_id=session_id,
        user_id=user_id,
        role=role,
        content_type=content_type,
        content_text=content_text,
        task_id=task_id,
        status=status_val,
        metadata_json=metadata_json,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return message


def update_message_status(
    db: Session,
    message_id: str,
    status_val: str,
    content_text: Optional[str] = None,
    metadata_json: Optional[dict] = None,
):
    """
    更新消息状态
    """
    message = db.query(ConversationMessage).filter(
        ConversationMessage.message_id == message_id
    ).first()

    if message:
        message.status = status_val
        if content_text is not None:
            message.content_text = content_text
        if metadata_json is not None:
            message.metadata_json = metadata_json
        db.commit()


def get_messages_by_session(
    db: Session,
    session_id: str,
) -> list:
    """
    查询会话的所有消息
    """
    return db.query(ConversationMessage).filter(
        ConversationMessage.session_id == session_id
    ).order_by(ConversationMessage.created_at.asc()).all()


def get_message_by_task_id(
    db: Session,
    task_id: str,
) -> Optional[ConversationMessage]:
    """
    根据任务ID查询关联的消息
    """
    return db.query(ConversationMessage).filter(
        ConversationMessage.task_id == task_id
    ).first()


# ======================== 媒体资源操作 ========================

def create_media_asset(
    db: Session,
    user_id: int,
    url: str,
    media_type: str,
    session_id: Optional[str] = None,
    message_id: Optional[str] = None,
    task_id: Optional[str] = None,
    provider: str = "qiniu",
    bucket: Optional[str] = None,
    object_key: Optional[str] = None,
    mime_type: Optional[str] = None,
    file_size: Optional[int] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> MediaAsset:
    """
    创建媒体资源记录
    """
    asset_id = _generate_asset_id()

    asset = MediaAsset(
        asset_id=asset_id,
        user_id=user_id,
        session_id=session_id,
        message_id=message_id,
        task_id=task_id,
        media_type=media_type,
        provider=provider,
        bucket=bucket,
        object_key=object_key,
        url=url,
        mime_type=mime_type,
        file_size=file_size,
        width=width,
        height=height,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    return asset


def get_assets_by_message(
    db: Session,
    message_id: str,
) -> list:
    """
    查询消息关联的媒体资源
    """
    return db.query(MediaAsset).filter(
        MediaAsset.message_id == message_id
    ).all()


def get_assets_by_session(
    db: Session,
    session_id: str,
) -> list:
    """
    查询会话关联的所有媒体资源
    """
    return db.query(MediaAsset).filter(
        MediaAsset.session_id == session_id
    ).all()
