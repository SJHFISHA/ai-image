"""
通用请求和响应模型
"""
from pydantic import BaseModel, Field
from typing import Generic, Optional, TypeVar, List

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一响应结构"""
    code: int = Field(0, description="业务状态码，0表示成功")
    message: str = Field("success", description="提示信息")
    data: Optional[T] = Field(None, description="业务数据")
    success: bool = Field(True, description="是否成功")


class PaginationParams(BaseModel):
    """分页请求参数"""
    page: int = Field(1, ge=1, description="页码，默认1")
    page_size: int = Field(20, ge=1, le=100, description="每页数量，默认20，最大100")


class PaginatedData(BaseModel, Generic[T]):
    """分页响应数据"""
    items: List[T] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
