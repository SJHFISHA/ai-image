"""
模型价格配置相关请求和响应模型
"""
from pydantic import BaseModel, Field
from typing import Optional


class ModelPriceConfigResponse(BaseModel):
    """模型价格配置响应"""
    price_config_id: int = Field(..., alias="id", description="价格配置ID")
    model_key: str = Field(..., description="模型标识")
    model_name: str = Field(..., description="模型名称")
    provider_key: str = Field(..., description="供应商标识")
    capability_type: str = Field(..., description="能力类型")
    image_size: Optional[str] = Field(None, description="图片尺寸")
    image_count: Optional[int] = Field(None, description="图片数量")
    video_duration: Optional[int] = Field(None, description="视频时长")
    video_resolution: Optional[str] = Field(None, description="视频分辨率")
    points: int = Field(..., description="消耗积分")

    class Config:
        from_attributes = True
        populate_by_name = True
        protected_namespaces = ()


class ModelPriceConfigListResponse(BaseModel):
    """模型价格配置列表响应"""
    total: int = Field(..., description="总数")
    items: list[ModelPriceConfigResponse] = Field(..., description="配置列表")
