"""
积分相关请求和响应模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PointBalanceResponse(BaseModel):
    """积分余额响应"""
    balance_points: int = Field(..., description="可用积分")
    frozen_points: int = Field(..., description="冻结积分")
    total_recharged_points: int = Field(..., description="累计充值积分")
    total_consumed_points: int = Field(..., description="累计消费积分")


class PointTransactionResponse(BaseModel):
    """积分流水响应"""
    transaction_no: str = Field(..., description="流水号")
    type: str = Field(..., description="类型")
    direction: str = Field(..., description="方向")
    points: int = Field(..., description="变动积分")
    balance_before: int = Field(..., description="变动前余额")
    balance_after: int = Field(..., description="变动后余额")
    frozen_before: int = Field(..., description="变动前冻结")
    frozen_after: int = Field(..., description="变动后冻结")
    related_order_no: Optional[str] = Field(None, description="关联订单号")
    related_task_id: Optional[str] = Field(None, description="关联任务ID")
    remark: Optional[str] = Field(None, description="备注")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class PointTransactionListResponse(BaseModel):
    """积分流水列表响应"""
    total: int = Field(..., description="总数")
    items: list[PointTransactionResponse] = Field(..., description="流水列表")
