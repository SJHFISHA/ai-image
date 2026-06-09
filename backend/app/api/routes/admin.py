"""
管理员相关路由
全部挂在 /api/admin 下
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_current_admin_user
from app.models.admin_user import AdminUser
from app.schemas.common import ApiResponse
from app.schemas.admin import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminInfo,
    ModelPriceConfigCreateRequest,
    ModelPriceConfigUpdateRequest,
    ModelPriceConfigDetailResponse,
    ModelPriceConfigListResponse,
    RechargePackageCreateRequest,
    RechargePackageUpdateRequest,
    RechargePackageDetailResponse,
    RechargePackageListResponse,
    RechargeOrderDetailResponse,
    RechargeOrderListResponse,
    RechargeOrderStatusUpdateRequest,
    PointAccountDetailResponse,
    PointAccountListResponse,
    AdminPointAdjustRequest,
    PointTransactionDetailResponse,
    PointTransactionListResponse,
)
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["后台管理"])


# ======================== 管理员认证 ========================

@router.post("/auth/login", response_model=ApiResponse[AdminLoginResponse], summary="管理员登录")
def admin_login(request: AdminLoginRequest, db: Session = Depends(get_db)):
    """
    管理员登录

    - username: 管理员用户名
    - password: 密码
    """
    result = admin_service.admin_login(
        db=db,
        username=request.username,
        password=request.password
    )

    response_data = AdminLoginResponse(**result)
    return ApiResponse(
        code=0,
        message="登录成功",
        data=response_data,
        success=True
    )


@router.get("/auth/me", response_model=ApiResponse[AdminInfo], summary="获取当前管理员信息")
def get_admin_me(current_admin: AdminUser = Depends(get_current_admin_user)):
    """获取当前登录管理员信息"""
    response_data = AdminInfo(
        id=current_admin.id,
        username=current_admin.username,
        nickname=current_admin.nickname,
        role=current_admin.role
    )
    return ApiResponse(
        code=0,
        message="success",
        data=response_data,
        success=True
    )


# ======================== 模型价格配置 CRUD ========================

@router.get("/model-prices", response_model=ApiResponse[ModelPriceConfigListResponse], summary="查询模型价格配置列表")
def get_model_price_configs(
    capability_type: Optional[str] = Query(None, description="能力类型筛选"),
    keyword: Optional[str] = Query(None, description="搜索关键词（模型标识/名称）"),
    enabled: Optional[int] = Query(None, description="启用状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """查询模型价格配置列表"""
    result = admin_service.get_model_price_config_list(
        db=db,
        capability_type=capability_type,
        keyword=keyword,
        enabled=enabled,
        page=page,
        page_size=page_size
    )

    items = [ModelPriceConfigDetailResponse.model_validate(item) for item in result["items"]]
    response_data = ModelPriceConfigListResponse(total=result["total"], items=items)
    return ApiResponse(data=response_data)


@router.post("/model-prices", response_model=ApiResponse[ModelPriceConfigDetailResponse], summary="创建模型价格配置")
def create_model_price_config(
    request: ModelPriceConfigCreateRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """创建模型价格配置"""
    config = admin_service.create_model_price_config(db=db, data=request.model_dump())
    response_data = ModelPriceConfigDetailResponse.model_validate(config)
    return ApiResponse(code=0, message="创建成功", data=response_data)


@router.put("/model-prices/{config_id}", response_model=ApiResponse[ModelPriceConfigDetailResponse], summary="更新模型价格配置")
def update_model_price_config(
    config_id: int,
    request: ModelPriceConfigUpdateRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """更新模型价格配置"""
    config = admin_service.update_model_price_config(
        db=db,
        config_id=config_id,
        data=request.model_dump(exclude_unset=True)
    )
    response_data = ModelPriceConfigDetailResponse.model_validate(config)
    return ApiResponse(code=0, message="更新成功", data=response_data)


@router.delete("/model-prices/{config_id}", response_model=ApiResponse, summary="删除模型价格配置")
def delete_model_price_config(
    config_id: int,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """删除模型价格配置"""
    admin_service.delete_model_price_config(db=db, config_id=config_id)
    return ApiResponse(code=0, message="删除成功")


# ======================== 充值套餐 CRUD ========================

@router.get("/recharge-packages", response_model=ApiResponse[RechargePackageListResponse], summary="查询充值套餐列表")
def get_recharge_packages(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    enabled: Optional[int] = Query(None, description="启用状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """查询充值套餐列表"""
    result = admin_service.get_recharge_package_list(
        db=db,
        keyword=keyword,
        enabled=enabled,
        page=page,
        page_size=page_size
    )

    items = [RechargePackageDetailResponse.model_validate(item) for item in result["items"]]
    response_data = RechargePackageListResponse(total=result["total"], items=items)
    return ApiResponse(data=response_data)


@router.post("/recharge-packages", response_model=ApiResponse[RechargePackageDetailResponse], summary="创建充值套餐")
def create_recharge_package(
    request: RechargePackageCreateRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """创建充值套餐"""
    package = admin_service.create_recharge_package(db=db, data=request.model_dump())
    response_data = RechargePackageDetailResponse.model_validate(package)
    return ApiResponse(code=0, message="创建成功", data=response_data)


@router.put("/recharge-packages/{package_id}", response_model=ApiResponse[RechargePackageDetailResponse], summary="更新充值套餐")
def update_recharge_package(
    package_id: int,
    request: RechargePackageUpdateRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """更新充值套餐"""
    package = admin_service.update_recharge_package(
        db=db,
        package_id=package_id,
        data=request.model_dump(exclude_unset=True)
    )
    response_data = RechargePackageDetailResponse.model_validate(package)
    return ApiResponse(code=0, message="更新成功", data=response_data)


@router.delete("/recharge-packages/{package_id}", response_model=ApiResponse, summary="删除充值套餐")
def delete_recharge_package(
    package_id: int,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """删除充值套餐"""
    admin_service.delete_recharge_package(db=db, package_id=package_id)
    return ApiResponse(code=0, message="删除成功")


# ======================== 充值订单 ========================

@router.get("/recharge-orders", response_model=ApiResponse[RechargeOrderListResponse], summary="查询充值订单列表")
def get_recharge_orders(
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    pay_status: Optional[str] = Query(None, description="支付状态筛选"),
    order_no: Optional[str] = Query(None, description="订单号搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """查询充值订单列表"""
    result = admin_service.get_recharge_order_list(
        db=db,
        user_id=user_id,
        pay_status=pay_status,
        order_no=order_no,
        page=page,
        page_size=page_size
    )

    items = [RechargeOrderDetailResponse.model_validate(item) for item in result["items"]]
    response_data = RechargeOrderListResponse(total=result["total"], items=items)
    return ApiResponse(data=response_data)


@router.put("/recharge-orders/{order_id}/status", response_model=ApiResponse[RechargeOrderDetailResponse], summary="更新订单状态")
def update_recharge_order_status(
    order_id: int,
    request: RechargeOrderStatusUpdateRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """更新充值订单支付状态"""
    order = admin_service.update_recharge_order_status(
        db=db,
        order_id=order_id,
        pay_status=request.pay_status
    )
    response_data = RechargeOrderDetailResponse.model_validate(order)
    return ApiResponse(code=0, message="更新成功", data=response_data)


# ======================== 用户积分账户 ========================

@router.get("/point-accounts", response_model=ApiResponse[PointAccountListResponse], summary="查询用户积分账户列表")
def get_point_accounts(
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    keyword: Optional[str] = Query(None, description="用户名搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """查询用户积分账户列表"""
    result = admin_service.get_point_account_list(
        db=db,
        user_id=user_id,
        keyword=keyword,
        page=page,
        page_size=page_size
    )

    items = [PointAccountDetailResponse(**item) for item in result["items"]]
    response_data = PointAccountListResponse(total=result["total"], items=items)
    return ApiResponse(data=response_data)


@router.post("/point-accounts/adjust", response_model=ApiResponse[PointAccountDetailResponse], summary="管理员调整用户积分")
def admin_adjust_points(
    request: AdminPointAdjustRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    管理员手动调整用户积分

    - user_id: 用户ID
    - points: 积分数量（正数增加，负数扣减）
    - remark: 调整原因
    """
    account = admin_service.admin_adjust_points(
        db=db,
        user_id=request.user_id,
        points=request.points,
        remark=request.remark
    )

    # 查询用户名
    from app.models.user import User
    user = db.query(User).filter(User.id == request.user_id).first()

    response_data = PointAccountDetailResponse(
        id=account.id,
        user_id=account.user_id,
        username=user.username if user else None,
        balance_points=account.balance_points,
        frozen_points=account.frozen_points,
        total_recharged_points=account.total_recharged_points,
        total_consumed_points=account.total_consumed_points,
        created_at=account.created_at,
        updated_at=account.updated_at
    )
    return ApiResponse(code=0, message="调整成功", data=response_data)


# ======================== 积分流水 ========================

@router.get("/point-transactions", response_model=ApiResponse[PointTransactionListResponse], summary="查询积分流水列表")
def get_point_transactions(
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    transaction_type: Optional[str] = Query(None, description="流水类型筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    查询积分流水列表

    - user_id: 用户ID筛选
    - transaction_type: 流水类型筛选（recharge, freeze, consume, refund, unfreeze, admin_adjust）
    """
    result = admin_service.get_point_transaction_list(
        db=db,
        user_id=user_id,
        transaction_type=transaction_type,
        page=page,
        page_size=page_size
    )

    items = [PointTransactionDetailResponse(**item) for item in result["items"]]
    response_data = PointTransactionListResponse(total=result["total"], items=items)
    return ApiResponse(data=response_data)
