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
    ModelConfigCreateRequest,
    ModelConfigUpdateRequest,
    ModelConfigDetailResponse,
    ModelConfigListResponse,
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
    AdminUserDetailResponse,
    AdminUserListResponse,
    AdminUserStatusUpdateRequest,
    AdminTaskDetailResponse,
    AdminTaskListResponse,
)
from app.schemas.notification import (
    AdminNotificationCreateRequest,
    AdminNotificationUpdateRequest,
    NotificationDetailResponse,
    NotificationListResponse,
)
from app.services import notification_service
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

# ======================== 通知管理 CRUD ========================

@router.get("/notifications", response_model=ApiResponse[NotificationListResponse], summary="查询通知列表")
def get_admin_notifications(
    keyword: Optional[str] = Query(None, description="搜索标题/内容"),
    status_filter: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    result = notification_service.get_admin_notification_list(
        db=db,
        keyword=keyword,
        status_filter=status_filter,
        page=page,
        page_size=page_size
    )
    items = [NotificationDetailResponse.model_validate(item) for item in result["items"]]
    return ApiResponse(data=NotificationListResponse(total=result["total"], items=items))


@router.post("/notifications", response_model=ApiResponse[NotificationDetailResponse], summary="创建通知")
def create_admin_notification(
    request: AdminNotificationCreateRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    notification = notification_service.create_admin_notification(
        db=db,
        data=request.model_dump(),
        admin_id=current_admin.id
    )
    return ApiResponse(code=0, message="创建成功", data=NotificationDetailResponse.model_validate(notification))


@router.put("/notifications/{notification_id}", response_model=ApiResponse[NotificationDetailResponse], summary="更新通知")
def update_admin_notification(
    notification_id: int,
    request: AdminNotificationUpdateRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    notification = notification_service.update_admin_notification(
        db=db,
        notification_id=notification_id,
        data=request.model_dump(exclude_unset=True)
    )
    return ApiResponse(code=0, message="更新成功", data=NotificationDetailResponse.model_validate(notification))


@router.delete("/notifications/{notification_id}", response_model=ApiResponse, summary="删除通知")
def delete_admin_notification(
    notification_id: int,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    notification_service.delete_admin_notification(db=db, notification_id=notification_id)
    return ApiResponse(code=0, message="删除成功")


@router.post("/notifications/{notification_id}/publish", response_model=ApiResponse[NotificationDetailResponse], summary="发布通知")
def publish_admin_notification(
    notification_id: int,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    notification = notification_service.publish_admin_notification(db=db, notification_id=notification_id)
    return ApiResponse(code=0, message="发布成功", data=NotificationDetailResponse.model_validate(notification))


@router.post("/notifications/{notification_id}/disable", response_model=ApiResponse[NotificationDetailResponse], summary="下架通知")
def disable_admin_notification(
    notification_id: int,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    notification = notification_service.disable_admin_notification(db=db, notification_id=notification_id)
    return ApiResponse(code=0, message="下架成功", data=NotificationDetailResponse.model_validate(notification))

# ======================== 模型配置 CRUD ========================

@router.get("/model-configs", response_model=ApiResponse[ModelConfigListResponse], summary="查询模型配置列表")
def get_model_configs(
    capability_type: Optional[str] = Query(None, description="能力类型筛选"),
    keyword: Optional[str] = Query(None, description="搜索关键词（模型标识/名称）"),
    enabled: Optional[int] = Query(None, description="启用状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """查询模型配置列表"""
    result = admin_service.get_model_config_list(
        db=db,
        capability_type=capability_type,
        keyword=keyword,
        enabled=enabled,
        page=page,
        page_size=page_size
    )

    items = [ModelConfigDetailResponse.model_validate(item) for item in result["items"]]
    response_data = ModelConfigListResponse(total=result["total"], items=items)
    return ApiResponse(data=response_data)


@router.post("/model-configs", response_model=ApiResponse[ModelConfigDetailResponse], summary="创建模型配置")
def create_model_config(
    request: ModelConfigCreateRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """创建模型配置"""
    config = admin_service.create_model_config(db=db, data=request.model_dump())
    response_data = ModelConfigDetailResponse.model_validate(config)
    return ApiResponse(code=0, message="创建成功", data=response_data)


@router.put("/model-configs/{config_id}", response_model=ApiResponse[ModelConfigDetailResponse], summary="更新模型配置")
def update_model_config(
    config_id: int,
    request: ModelConfigUpdateRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """更新模型配置"""
    config = admin_service.update_model_config(
        db=db,
        config_id=config_id,
        data=request.model_dump(exclude_unset=True)
    )
    response_data = ModelConfigDetailResponse.model_validate(config)
    return ApiResponse(code=0, message="更新成功", data=response_data)


@router.delete("/model-configs/{config_id}", response_model=ApiResponse, summary="删除模型配置")
def delete_model_config(
    config_id: int,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """删除模型配置"""
    admin_service.delete_model_config(db=db, config_id=config_id)
    return ApiResponse(code=0, message="删除成功")


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

    items = [
        ModelPriceConfigDetailResponse(
            id=item.id,
            model_id=item.model_id,
            model_key=item.model_config.model_key,
            model_name=item.model_config.model_name,
            capability_type=item.model_config.capability_type,
            provider_key=item.model_config.provider_key,
            billing_mode=item.billing_mode,
            image_size=item.image_size,
            image_count=item.image_count,
            aspect_ratio=item.aspect_ratio,
            video_duration=item.video_duration,
            video_resolution=item.video_resolution,
            points=item.points,
            cost_amount=item.cost_amount,
            cost_currency=item.cost_currency,
            enabled=item.enabled,
            sort_order=item.sort_order,
            remark=item.remark,
            created_at=item.created_at,
            updated_at=item.updated_at
        )
        for item in result["items"]
    ]
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
    response_data = ModelPriceConfigDetailResponse(
        id=config.id,
        model_id=config.model_id,
        model_key=config.model_config.model_key,
        model_name=config.model_config.model_name,
        capability_type=config.model_config.capability_type,
        provider_key=config.model_config.provider_key,
        billing_mode=config.billing_mode,
        image_size=config.image_size,
        image_count=config.image_count,
        aspect_ratio=config.aspect_ratio,
        video_duration=config.video_duration,
        video_resolution=config.video_resolution,
        points=config.points,
        cost_amount=config.cost_amount,
        cost_currency=config.cost_currency,
        enabled=config.enabled,
        sort_order=config.sort_order,
        remark=config.remark,
        created_at=config.created_at,
        updated_at=config.updated_at
    )
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
    response_data = ModelPriceConfigDetailResponse(
        id=config.id,
        model_id=config.model_id,
        model_key=config.model_config.model_key,
        model_name=config.model_config.model_name,
        capability_type=config.model_config.capability_type,
        provider_key=config.model_config.provider_key,
        billing_mode=config.billing_mode,
        image_size=config.image_size,
        image_count=config.image_count,
        aspect_ratio=config.aspect_ratio,
        video_duration=config.video_duration,
        video_resolution=config.video_resolution,
        points=config.points,
        cost_amount=config.cost_amount,
        cost_currency=config.cost_currency,
        enabled=config.enabled,
        sort_order=config.sort_order,
        remark=config.remark,
        created_at=config.created_at,
        updated_at=config.updated_at
    )
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


# ======================== 用户管理 ========================

@router.get("/users", response_model=ApiResponse[AdminUserListResponse], summary="查询用户列表")
def get_users(
    keyword: Optional[str] = Query(None, description="搜索关键词（用户名/昵称）"),
    status: Optional[str] = Query(None, description="状态筛选: normal, disabled"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """查询用户列表"""
    result = admin_service.get_user_list(
        db=db,
        keyword=keyword,
        status_filter=status,
        page=page,
        page_size=page_size
    )

    items = [AdminUserDetailResponse.model_validate(item) for item in result["items"]]
    response_data = AdminUserListResponse(total=result["total"], items=items)
    return ApiResponse(data=response_data)


@router.put("/users/{user_id}/status", response_model=ApiResponse[AdminUserDetailResponse], summary="更新用户状态")
def update_user_status(
    user_id: int,
    request: AdminUserStatusUpdateRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """更新用户状态（启用/禁用）"""
    user = admin_service.update_user_status(
        db=db,
        user_id=user_id,
        new_status=request.status
    )
    response_data = AdminUserDetailResponse.model_validate(user)
    return ApiResponse(code=0, message="更新成功", data=response_data)


# ======================== 生成任务管理 ========================

@router.get("/tasks", response_model=ApiResponse[AdminTaskListResponse], summary="查询生成任务列表")
def get_generation_tasks(
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    status: Optional[str] = Query(None, description="任务状态筛选"),
    task_id: Optional[str] = Query(None, description="任务ID搜索"),
    keyword: Optional[str] = Query(None, description="关键词搜索（任务ID/模型/提示词）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """查询生成任务列表"""
    result = admin_service.get_generation_task_list(
        db=db,
        user_id=user_id,
        task_status=status,
        task_id=task_id,
        keyword=keyword,
        page=page,
        page_size=page_size
    )

    items = [AdminTaskDetailResponse(**item) for item in result["items"]]
    response_data = AdminTaskListResponse(total=result["total"], items=items)
    return ApiResponse(data=response_data)
