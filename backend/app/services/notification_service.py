"""
系统通知业务逻辑
"""
import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.notification import SystemNotification, UserNotificationRead
from app.utils.timezone import now_beijing_naive


def _active_notification_query(db: Session):
    now = now_beijing_naive()
    return db.query(SystemNotification).filter(
        SystemNotification.status == "published",
        or_(SystemNotification.publish_at.is_(None), SystemNotification.publish_at <= now),
        or_(SystemNotification.expire_at.is_(None), SystemNotification.expire_at > now),
    )


def get_user_notification_list(db: Session, user_id: int, page: int = 1, page_size: int = 20) -> dict:
    query = _active_notification_query(db)

    total = query.count()
    notifications = query.order_by(
        SystemNotification.publish_at.desc(),
        SystemNotification.id.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    notification_ids = [item.notification_id for item in notifications]
    read_ids = set()
    if notification_ids:
        rows = db.query(UserNotificationRead.notification_id).filter(
            UserNotificationRead.user_id == user_id,
            UserNotificationRead.notification_id.in_(notification_ids)
        ).all()
        read_ids = {row[0] for row in rows}

    items = []
    for item in notifications:
        item.is_read = item.notification_id in read_ids
        items.append(item)

    return {"total": total, "items": items}


def get_unread_count(db: Session, user_id: int) -> int:
    query = _active_notification_query(db).outerjoin(
        UserNotificationRead,
        and_(
            UserNotificationRead.notification_id == SystemNotification.notification_id,
            UserNotificationRead.user_id == user_id,
        )
    ).filter(UserNotificationRead.id.is_(None))

    return query.count()


def mark_notification_read(db: Session, user_id: int, notification_id: str):
    notification = _active_notification_query(db).filter(
        SystemNotification.notification_id == notification_id
    ).first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在或已失效"
        )

    exists = db.query(UserNotificationRead).filter(
        UserNotificationRead.user_id == user_id,
        UserNotificationRead.notification_id == notification_id
    ).first()
    if exists:
        return exists

    read = UserNotificationRead(
        user_id=user_id,
        notification_id=notification_id,
        read_at=now_beijing_naive()
    )
    db.add(read)
    db.commit()
    db.refresh(read)
    return read


def mark_all_notifications_read(db: Session, user_id: int) -> int:
    notifications = _active_notification_query(db).all()
    notification_ids = [item.notification_id for item in notifications]
    if not notification_ids:
        return 0

    existing_rows = db.query(UserNotificationRead.notification_id).filter(
        UserNotificationRead.user_id == user_id,
        UserNotificationRead.notification_id.in_(notification_ids)
    ).all()
    existing_ids = {row[0] for row in existing_rows}

    created_count = 0
    now = now_beijing_naive()
    for notification_id in notification_ids:
        if notification_id in existing_ids:
            continue
        db.add(UserNotificationRead(
            user_id=user_id,
            notification_id=notification_id,
            read_at=now
        ))
        created_count += 1

    db.commit()
    return created_count


def get_admin_notification_list(
    db: Session,
    keyword: Optional[str] = None,
    status_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> dict:
    query = db.query(SystemNotification)

    if keyword:
        query = query.filter(
            SystemNotification.title.contains(keyword) |
            SystemNotification.content.contains(keyword)
        )
    if status_filter:
        query = query.filter(SystemNotification.status == status_filter)

    total = query.count()
    items = query.order_by(
        SystemNotification.id.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    return {"total": total, "items": items}


def create_admin_notification(db: Session, data: dict, admin_id: int) -> SystemNotification:
    data = {key: value for key, value in data.items() if value is not None}
    status_value = data.get("status", "draft")
    if status_value == "published" and data.get("publish_at") is None:
        data["publish_at"] = now_beijing_naive()

    notification = SystemNotification(
        notification_id=uuid.uuid4().hex,
        created_by=admin_id,
        **data
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def update_admin_notification(db: Session, notification_id: int, data: dict) -> SystemNotification:
    notification = db.query(SystemNotification).filter(SystemNotification.id == notification_id).first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在"
        )

    for key, value in data.items():
        if value is not None:
            setattr(notification, key, value)

    if notification.status == "published" and notification.publish_at is None:
        notification.publish_at = now_beijing_naive()

    notification.updated_at = now_beijing_naive()
    db.commit()
    db.refresh(notification)
    return notification


def delete_admin_notification(db: Session, notification_id: int):
    notification = db.query(SystemNotification).filter(SystemNotification.id == notification_id).first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在"
        )

    db.delete(notification)
    db.commit()


def publish_admin_notification(db: Session, notification_id: int) -> SystemNotification:
    return update_admin_notification(db, notification_id, {
        "status": "published",
        "publish_at": now_beijing_naive()
    })


def disable_admin_notification(db: Session, notification_id: int) -> SystemNotification:
    return update_admin_notification(db, notification_id, {
        "status": "disabled"
    })