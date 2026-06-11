"""
管理员相关请求和响应模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ======================== 管理员认证 ========================

class AdminLoginRequest(BaseModel):
    """管理员登录请求"""
    username: str = Field(..., description="管理员用户名")
    password: str = Field(..., description="密码")


class AdminInfo(BaseModel):
    """管理员信息"""
    id: int = Field(..., description="管理员ID")
    username: str = Field(..., description="用户名")
    nickname: Optional[str] = Field(None, description="昵称")
    role: str = Field(..., description="角色: admin, super_admin")

    class Config:
        from_attributes = True


class AdminLoginResponse(BaseModel):
    """管理员登录响应"""
    access_token: str = Field(..., description="JWT token")
    token_type: str = Field("Bearer", description="token类型")
    admin: AdminInfo = Field(..., description="管理员信息")


# ======================== 模型配置 CRUD ========================

class ModelConfigCreateRequest(BaseModel):
    """创建模型配置"""
    model_key: str = Field(..., max_length=128, description="真实模型标识")
    model_name: str = Field(..., max_length=128, description="前端展示名称")
    provider_key: str = Field(..., max_length=64, description="供应商标识")
    route_mode: Optional[str] = Field(None, max_length=32, description="路由模式: price, speed, success_rate")
    capability_type: str = Field(..., description="能力类型: image, video, text, audio")
    enabled: int = Field(1, description="是否启用: 1=启用, 0=禁用")
    sort_order: int = Field(0, description="排序")
    remark: Optional[str] = Field(None, max_length=255, description="备注")


class ModelConfigUpdateRequest(BaseModel):
    """更新模型配置"""
    model_key: Optional[str] = Field(None, max_length=128, description="真实模型标识")
    model_name: Optional[str] = Field(None, max_length=128, description="前端展示名称")
    provider_key: Optional[str] = Field(None, max_length=64, description="供应商标识")
    route_mode: Optional[str] = Field(None, max_length=32, description="路由模式")
    capability_type: Optional[str] = Field(None, description="能力类型")
    enabled: Optional[int] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序")
    remark: Optional[str] = Field(None, max_length=255, description="备注")


class ModelConfigDetailResponse(BaseModel):
    """模型配置详情"""
    id: int = Field(..., description="配置ID")
    model_key: str = Field(..., description="真实模型标识")
    model_name: str = Field(..., description="前端展示名称")
    provider_key: str = Field(..., description="供应商标识")
    route_mode: Optional[str] = Field(None, description="路由模式")
    capability_type: str = Field(..., description="能力类型")
    enabled: int = Field(..., description="是否启用")
    sort_order: int = Field(..., description="排序")
    remark: Optional[str] = Field(None, description="备注")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ModelConfigListResponse(BaseModel):
    """模型配置列表"""
    total: int = Field(..., description="总数")
    items: List[ModelConfigDetailResponse] = Field(..., description="配置列表")


# ======================== 模型价格配置 CRUD ========================

class ModelPriceConfigCreateRequest(BaseModel):
    """创建模型价格配置"""
    model_id: int = Field(..., description="关联 model_configs.id")
    billing_mode: str = Field("fixed", max_length=32, description="计费方式")
    image_size: Optional[str] = Field(None, max_length=32, description="图片尺寸")
    image_count: int = Field(1, ge=1, description="生成图片数量")
    video_duration: Optional[int] = Field(None, ge=1, description="视频时长")
    video_resolution: Optional[str] = Field(None, max_length=32, description="视频分辨率")
    points: int = Field(..., ge=0, description="用户消耗积分")
    cost_amount: Optional[Decimal] = Field(None, description="预估真实成本")
    cost_currency: str = Field("CNY", max_length=16, description="成本货币")
    enabled: int = Field(1, description="是否启用: 1=启用, 0=禁用")
    sort_order: int = Field(0, description="排序")
    remark: Optional[str] = Field(None, max_length=255, description="备注")


class ModelPriceConfigUpdateRequest(BaseModel):
    """更新模型价格配置"""
    model_id: Optional[int] = Field(None, description="关联 model_configs.id")
    billing_mode: Optional[str] = Field(None, max_length=32, description="计费方式")
    image_size: Optional[str] = Field(None, max_length=32, description="图片尺寸")
    image_count: Optional[int] = Field(None, ge=1, description="生成图片数量")
    video_duration: Optional[int] = Field(None, ge=1, description="视频时长")
    video_resolution: Optional[str] = Field(None, max_length=32, description="视频分辨率")
    points: Optional[int] = Field(None, ge=0, description="用户消耗积分")
    cost_amount: Optional[Decimal] = Field(None, description="预估真实成本")
    cost_currency: Optional[str] = Field(None, max_length=16, description="成本货币")
    enabled: Optional[int] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序")
    remark: Optional[str] = Field(None, max_length=255, description="备注")


class ModelPriceConfigDetailResponse(BaseModel):
    """模型价格配置详情"""
    id: int = Field(..., description="配置ID")
    model_id: int = Field(..., description="关联模型配置ID")
    model_key: str = Field(..., description="模型标识")
    model_name: str = Field(..., description="模型名称")
    capability_type: str = Field(..., description="能力类型")
    provider_key: str = Field(..., description="供应商标识")
    billing_mode: str = Field(..., description="计费方式")
    image_size: Optional[str] = Field(None, description="图片尺寸")
    image_count: int = Field(..., description="生成图片数量")
    video_duration: Optional[int] = Field(None, description="视频时长")
    video_resolution: Optional[str] = Field(None, description="视频分辨率")
    points: int = Field(..., description="用户消耗积分")
    cost_amount: Optional[Decimal] = Field(None, description="预估真实成本")
    cost_currency: str = Field(..., description="成本货币")
    enabled: int = Field(..., description="是否启用")
    sort_order: int = Field(..., description="排序")
    remark: Optional[str] = Field(None, description="备注")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ModelPriceConfigListResponse(BaseModel):
    """模型价格配置列表"""
    total: int = Field(..., description="总数")
    items: List[ModelPriceConfigDetailResponse] = Field(..., description="配置列表")


# ======================== 充值套餐 CRUD ========================

class RechargePackageCreateRequest(BaseModel):
    """创建充值套餐"""
    package_name: str = Field(..., max_length=64, description="套餐名称")
    amount: Decimal = Field(..., description="充值金额")
    base_points: int = Field(..., ge=0, description="基础积分")
    bonus_points: int = Field(0, ge=0, description="赠送积分")
    total_points: int = Field(..., ge=0, description="总积分")
    enabled: int = Field(1, description="是否启用: 1=启用, 0=禁用")
    sort_order: int = Field(0, description="排序")


class RechargePackageUpdateRequest(BaseModel):
    """更新充值套餐"""
    package_name: Optional[str] = Field(None, max_length=64, description="套餐名称")
    amount: Optional[Decimal] = Field(None, description="充值金额")
    base_points: Optional[int] = Field(None, ge=0, description="基础积分")
    bonus_points: Optional[int] = Field(None, ge=0, description="赠送积分")
    total_points: Optional[int] = Field(None, ge=0, description="总积分")
    enabled: Optional[int] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序")


class RechargePackageDetailResponse(BaseModel):
    """充值套餐详情"""
    id: int = Field(..., description="套餐ID")
    package_name: str = Field(..., description="套餐名称")
    amount: Decimal = Field(..., description="充值金额")
    base_points: int = Field(..., description="基础积分")
    bonus_points: int = Field(..., description="赠送积分")
    total_points: int = Field(..., description="总积分")
    enabled: int = Field(..., description="是否启用")
    sort_order: int = Field(..., description="排序")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class RechargePackageListResponse(BaseModel):
    """充值套餐列表"""
    total: int = Field(..., description="总数")
    items: List[RechargePackageDetailResponse] = Field(..., description="套餐列表")


# ======================== 充值订单 ========================

class RechargeOrderDetailResponse(BaseModel):
    """充值订单详情"""
    id: int = Field(..., description="订单ID")
    order_no: str = Field(..., description="订单号")
    user_id: int = Field(..., description="用户ID")
    package_id: int = Field(..., description="套餐ID")
    package_name: str = Field(..., description="套餐名称")
    amount: Decimal = Field(..., description="支付金额")
    currency: str = Field(..., description="货币类型")
    base_points: int = Field(..., description="基础积分")
    bonus_points: int = Field(..., description="赠送积分")
    total_points: int = Field(..., description="总到账积分")
    pay_channel: Optional[str] = Field(None, description="支付渠道")
    pay_status: str = Field(..., description="支付状态")
    pay_trade_no: Optional[str] = Field(None, description="第三方支付流水号")
    paid_at: Optional[datetime] = Field(None, description="支付成功时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class RechargeOrderListResponse(BaseModel):
    """充值订单列表"""
    total: int = Field(..., description="总数")
    items: List[RechargeOrderDetailResponse] = Field(..., description="订单列表")


class RechargeOrderStatusUpdateRequest(BaseModel):
    """更新充值订单状态"""
    pay_status: str = Field(..., description="支付状态: pending, paid, failed, closed, refunded")


# ======================== 用户积分账户 ========================

class PointAccountDetailResponse(BaseModel):
    """用户积分账户详情"""
    id: int = Field(..., description="账户ID")
    user_id: int = Field(..., description="用户ID")
    username: Optional[str] = Field(None, description="用户名（关联查询）")
    balance_points: int = Field(..., description="可用积分")
    frozen_points: int = Field(..., description="冻结积分")
    total_recharged_points: int = Field(..., description="累计充值积分")
    total_consumed_points: int = Field(..., description="累计消费积分")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class PointAccountListResponse(BaseModel):
    """用户积分账户列表"""
    total: int = Field(..., description="总数")
    items: List[PointAccountDetailResponse] = Field(..., description="账户列表")


class AdminPointAdjustRequest(BaseModel):
    """管理员调整用户积分"""
    user_id: int = Field(..., description="用户ID")
    points: int = Field(..., description="积分数量（正数增加，负数扣减）")
    remark: str = Field(..., min_length=1, max_length=255, description="调整原因")


# ======================== 积分流水 ========================

class PointTransactionDetailResponse(BaseModel):
    """积分流水详情"""
    id: int = Field(..., description="流水ID")
    transaction_no: str = Field(..., description="流水号")
    user_id: int = Field(..., description="用户ID")
    username: Optional[str] = Field(None, description="用户名（关联查询）")
    type: str = Field(..., description="类型")
    direction: str = Field(..., description="方向")
    points: int = Field(..., description="变动积分")
    balance_before: int = Field(..., description="变动前可用积分")
    balance_after: int = Field(..., description="变动后可用积分")
    frozen_before: int = Field(..., description="变动前冻结积分")
    frozen_after: int = Field(..., description="变动后冻结积分")
    related_order_no: Optional[str] = Field(None, description="关联订单号")
    related_task_id: Optional[str] = Field(None, description="关联任务ID")
    remark: Optional[str] = Field(None, description="备注")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class PointTransactionListResponse(BaseModel):
    """积分流水列表"""
    total: int = Field(..., description="总数")
    items: List[PointTransactionDetailResponse] = Field(..., description="流水列表")


# ======================== 用户管理 ========================

class AdminUserDetailResponse(BaseModel):
    """用户详情"""
    id: int = Field(..., description="用户ID")
    username: Optional[str] = Field(None, description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    status: str = Field(..., description="状态: normal, disabled")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class AdminUserListResponse(BaseModel):
    """用户列表"""
    total: int = Field(..., description="总数")
    items: List[AdminUserDetailResponse] = Field(..., description="用户列表")


class AdminUserStatusUpdateRequest(BaseModel):
    """更新用户状态"""
    status: str = Field(..., description="状态: normal, disabled")


# ======================== 生成任务管理 ========================

class AdminTaskDetailResponse(BaseModel):
    """生成任务详情"""
    id: int = Field(..., description="记录ID")
    task_id: str = Field(..., description="任务ID")
    user_id: int = Field(..., description="用户ID")
    username: Optional[str] = Field(None, description="用户名（关联查询）")
    price_config_id: int = Field(..., description="价格配置ID")
    model_key: str = Field(..., description="模型标识")
    model_name: str = Field(..., description="模型名称")
    capability_type: str = Field(..., description="能力类型")
    image_size: Optional[str] = Field(None, description="图片尺寸")
    image_count: Optional[int] = Field(None, description="图片数量")
    status: str = Field(..., description="任务状态")
    frozen_points: int = Field(..., description="冻结积分")
    consumed_points: int = Field(..., description="消费积分")
    refunded_points: int = Field(..., description="退回积分")
    prompt: Optional[str] = Field(None, description="提示词")
    error_message: Optional[str] = Field(None, description="错误信息")
    request_json: Optional[dict] = Field(None, description="请求参数")
    provider_response_json: Optional[dict] = Field(None, description="供应商原始响应")
    created_at: datetime = Field(..., description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始执行时间")
    finished_at: Optional[datetime] = Field(None, description="完成时间")

    class Config:
        from_attributes = True


class AdminTaskListResponse(BaseModel):
    """生成任务列表"""
    total: int = Field(..., description="总数")
    items: List[AdminTaskDetailResponse] = Field(..., description="任务列表")
