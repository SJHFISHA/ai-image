"""
系统通知请求和响应模型
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class NotificationDetailResponse(BaseModel):
    id: int
    notification_id: str
    title: str
    content: str
    type: str
    level: str
    status: str
    target_type: str
    publish_at: Optional[datetime] = None
    expire_at: Optional[datetime] = None
    is_read: Optional[bool] = False
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    total: int
    items: List[NotificationDetailResponse]


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int


class AdminNotificationCreateRequest(BaseModel):
    title: str = Field(..., max_length=128)
    content: str
    type: str = Field("system", max_length=32)
    level: str = Field("info", max_length=32)
    status: str = Field("draft", max_length=32)
    target_type: str = Field("all", max_length=32)
    publish_at: Optional[datetime] = None
    expire_at: Optional[datetime] = None


class AdminNotificationUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=128)
    content: Optional[str] = None
    type: Optional[str] = Field(None, max_length=32)
    level: Optional[str] = Field(None, max_length=32)
    status: Optional[str] = Field(None, max_length=32)
    target_type: Optional[str] = Field(None, max_length=32)
    publish_at: Optional[datetime] = None
    expire_at: Optional[datetime] = None