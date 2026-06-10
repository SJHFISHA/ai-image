"""
会话相关请求和响应模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ======================== 会话 ========================

class ConversationCreateRequest(BaseModel):
    """创建会话请求"""
    session_type: str = Field("mixed", description="会话类型: chat, image, video, mixed")
    title: Optional[str] = Field(None, max_length=255, description="会话标题")


class ConversationItem(BaseModel):
    """会话列表项"""
    session_id: str = Field(..., description="会话ID")
    title: Optional[str] = Field(None, description="会话标题")
    session_type: str = Field(..., description="会话类型")
    last_message_preview: Optional[str] = Field(None, description="最后消息预览")
    last_message_at: Optional[datetime] = Field(None, description="最后消息时间")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """会话列表响应"""
    total: int = Field(..., description="总数")
    items: List[ConversationItem] = Field(..., description="会话列表")


# ======================== 消息 ========================

class MediaAssetResponse(BaseModel):
    """媒体资源响应"""
    asset_id: str = Field(..., description="资源ID")
    media_type: str = Field(..., description="媒体类型")
    url: str = Field(..., description="访问URL")
    mime_type: Optional[str] = Field(None, description="MIME类型")
    file_size: Optional[int] = Field(None, description="文件大小")
    width: Optional[int] = Field(None, description="宽度")
    height: Optional[int] = Field(None, description="高度")

    class Config:
        from_attributes = True


class ConversationMessageResponse(BaseModel):
    """消息响应"""
    message_id: str = Field(..., description="消息ID")
    role: str = Field(..., description="角色: user, assistant, system")
    content_type: str = Field(..., description="内容类型: text, image, video, mixed")
    content_text: Optional[str] = Field(None, description="文本内容")
    task_id: Optional[str] = Field(None, description="关联任务ID")
    status: str = Field(..., description="状态: pending, running, success, failed")
    metadata_json: Optional[dict] = Field(None, description="扩展信息")
    assets: List[MediaAssetResponse] = Field(default_factory=list, description="关联媒体资源")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class ConversationDetailResponse(BaseModel):
    """会话详情响应"""
    session_id: str = Field(..., description="会话ID")
    title: Optional[str] = Field(None, description="会话标题")
    session_type: str = Field(..., description="会话类型")
    messages: List[ConversationMessageResponse] = Field(default_factory=list, description="消息列表")

    class Config:
        from_attributes = True
