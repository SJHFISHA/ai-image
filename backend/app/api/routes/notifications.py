"""
用户通知接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.notification import (
    NotificationDetailResponse,
    NotificationListResponse,
    NotificationUnreadCountResponse,
)
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["通知"])


@router.get("", response_model=ApiResponse[NotificationListResponse], summary="获取用户通知列表")
def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = notification_service.get_user_notification_list(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )

    items = [
        NotificationDetailResponse.model_validate(item)
        for item in result["items"]
    ]
    return ApiResponse(data=NotificationListResponse(total=result["total"], items=items))


@router.get("/unread-count", response_model=ApiResponse[NotificationUnreadCountResponse], summary="获取未读通知数")
def get_notification_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    unread_count = notification_service.get_unread_count(db=db, user_id=current_user.id)
    return ApiResponse(data=NotificationUnreadCountResponse(unread_count=unread_count))


@router.post("/{notification_id}/read", response_model=ApiResponse, summary="标记单条通知已读")
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notification_service.mark_notification_read(
        db=db,
        user_id=current_user.id,
        notification_id=notification_id
    )
    return ApiResponse(code=0, message="标记成功")


@router.post("/read-all", response_model=ApiResponse, summary="全部通知标记已读")
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notification_service.mark_all_notifications_read(db=db, user_id=current_user.id)
    return ApiResponse(code=0, message="标记成功")