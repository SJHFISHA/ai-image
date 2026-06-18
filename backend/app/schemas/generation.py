"""
生成任务相关请求和响应模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ImageGenerateRequest(BaseModel):
    """生图任务创建请求"""
    session_id: Optional[str] = Field(None, description="会话ID，不传则自动创建新会话")
    price_config_id: int = Field(..., description="模型价格配置ID")
    prompt: str = Field(..., min_length=1, max_length=2000, description="提示词")

class ImageEditRequest(BaseModel):
    """图片编辑任务创建请求"""
    session_id: Optional[str] = Field(None, description="会话ID")
    price_config_id: int = Field(..., description="模型价格配置ID")
    prompt: str = Field(..., min_length=1, max_length=2000, description="编辑提示词")
    image_urls: List[str] = Field(..., min_length=1, max_length=2, description="参考图片URL列表")


class ReferenceImageUploadResponse(BaseModel):
    """参考图片上传响应"""
    asset_id: str = Field(..., description="资源ID")
    url: str = Field(..., description="图片URL")

class TaskCreateResponse(BaseModel):
    """任务创建成功响应"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    frozen_points: int = Field(..., description="冻结积分")
    error_message: Optional[str] = Field(None, description="错误信息，仅在任务创建失败时返回")
    session_id: Optional[str] = Field(None, description="会话ID")


class TaskDetailResponse(BaseModel):
    """任务详情响应"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    model_key: str = Field(..., description="模型标识")
    model_name: str = Field(..., description="模型名称")
    capability_type: str = Field(..., description="能力类型")
    image_size: Optional[str] = Field(None, description="图片尺寸")
    image_count: Optional[int] = Field(None, description="图片数量")
    aspect_ratio: Optional[str] = Field(None, description="宽高比")
    prompt: Optional[str] = Field(None, description="提示词")
    frozen_points: int = Field(..., description="冻结积分")
    consumed_points: int = Field(..., description="消耗积分")
    refunded_points: int = Field(..., description="退回积分")
    error_message: Optional[str] = Field(None, description="错误信息")
    images: Optional[List[str]] = Field(None, description="生成的图片URL列表")
    created_at: datetime = Field(..., description="创建时间")
    finished_at: Optional[datetime] = Field(None, description="完成时间")

    class Config:
        from_attributes = True
        protected_namespaces = ()


class TaskListResponse(BaseModel):
    """任务列表响应"""
    total: int = Field(..., description="总数")
    items: list[TaskDetailResponse] = Field(..., description="任务列表")

class AssetItemResponse(BaseModel):
    """资产项"""
    id: int = Field(..., description="资产记录ID")
    asset_id: str = Field(..., description="资产ID")
    task_id: str = Field(..., description="任务ID")
    type: str = Field(..., description="资产类型: image, video, audio")
    url: str = Field(..., description="资源URL")
    cover_url: Optional[str] = Field(None, description="封面URL")
    title: Optional[str] = Field(None, description="标题")
    prompt: Optional[str] = Field(None, description="提示词")
    model_name: Optional[str] = Field(None, description="模型名称")
    created_at: datetime = Field(..., description="创建时间")
    class Config:
        protected_namespaces = ()


class AssetListResponse(BaseModel):
    """资产列表"""
    total: int = Field(..., description="总数")
    items: List[AssetItemResponse] = Field(..., description="资产列表")
