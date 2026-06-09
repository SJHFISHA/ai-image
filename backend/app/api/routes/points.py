"""
积分相关路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.point import (
    PointBalanceResponse,
    PointTransactionResponse,
    PointTransactionListResponse
)
from app.services import point_service

router = APIRouter(prefix="/user", tags=["积分"])


@router.get("/points", response_model=PointBalanceResponse, summary="查询积分余额")
def get_points(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    查询我的积分余额

    需要在请求头中携带: Authorization: Bearer <token>
    """
    balance = point_service.get_point_balance(db, current_user.id)
    return PointBalanceResponse(**balance)


@router.get("/point-logs", response_model=PointTransactionListResponse, summary="查询积分流水")
def get_point_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    查询我的积分流水

    - page: 页码（默认1）
    - page_size: 每页数量（默认20，最大100）

    需要在请求头中携带: Authorization: Bearer <token>
    """
    result = point_service.get_point_transactions(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )

    return PointTransactionListResponse(
        total=result["total"],
        items=[PointTransactionResponse.model_validate(t) for t in result["items"]]
    )
