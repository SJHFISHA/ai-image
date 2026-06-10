"""
管理员业务逻辑模块
"""
from typing import Optional
from datetime import datetime
from app.utils.timezone import now_beijing_naive

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.admin_user import AdminUser
from app.models.user import User
from app.models.model_price import ModelPriceConfig
from app.models.recharge import RechargePackage, RechargeOrder
from app.models.point import UserPointAccount, PointTransaction
from app.core.security import verify_password, create_admin_access_token
from app.utils.id_generator import generate_transaction_no
from app.utils.logger import app_logger


# ======================== 管理员认证 ========================

def admin_login(db: Session, username: str, password: str) -> dict:
    """
    管理员登录

    Returns:
        包含 access_token 和管理员信息的字典
    """
    admin = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    if admin.status != "normal":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员账号已被禁用"
        )

    if not verify_password(password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 更新最后登录时间
    admin.last_login_at = now_beijing_naive()
    db.commit()

    # 生成管理员JWT token
    access_token = create_admin_access_token(
        data={"sub": str(admin.id), "username": admin.username}
    )

    app_logger.info(f"管理员登录成功: username={username}, admin_id={admin.id}")

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "admin": {
            "id": admin.id,
            "username": admin.username,
            "nickname": admin.nickname,
            "role": admin.role
        }
    }


# ======================== 模型价格配置 CRUD ========================

def get_model_price_config_list(
    db: Session,
    capability_type: Optional[str] = None,
    keyword: Optional[str] = None,
    enabled: Optional[int] = None,
    page: int = 1,
    page_size: int = 20
) -> dict:
    """查询模型价格配置列表"""
    query = db.query(ModelPriceConfig)

    if capability_type:
        query = query.filter(ModelPriceConfig.capability_type == capability_type)
    if keyword:
        query = query.filter(
            ModelPriceConfig.model_key.contains(keyword) |
            ModelPriceConfig.model_name.contains(keyword)
        )
    if enabled is not None:
        query = query.filter(ModelPriceConfig.enabled == enabled)

    total = query.count()
    items = query.order_by(
        ModelPriceConfig.sort_order.asc(),
        ModelPriceConfig.id.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    return {"total": total, "items": items}


def create_model_price_config(db: Session, data: dict) -> ModelPriceConfig:
    """创建模型价格配置"""
    config = ModelPriceConfig(**data)
    db.add(config)
    db.commit()
    db.refresh(config)

    app_logger.info(f"创建模型价格配置: id={config.id}, model_key={config.model_key}")
    return config


def update_model_price_config(db: Session, config_id: int, data: dict) -> ModelPriceConfig:
    """更新模型价格配置"""
    config = db.query(ModelPriceConfig).filter(ModelPriceConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )

    for key, value in data.items():
        if value is not None:
            setattr(config, key, value)

    config.updated_at = now_beijing_naive()
    db.commit()
    db.refresh(config)

    app_logger.info(f"更新模型价格配置: id={config_id}")
    return config


def delete_model_price_config(db: Session, config_id: int):
    """删除模型价格配置"""
    config = db.query(ModelPriceConfig).filter(ModelPriceConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )

    db.delete(config)
    db.commit()

    app_logger.info(f"删除模型价格配置: id={config_id}")


# ======================== 充值套餐 CRUD ========================

def get_recharge_package_list(
    db: Session,
    keyword: Optional[str] = None,
    enabled: Optional[int] = None,
    page: int = 1,
    page_size: int = 20
) -> dict:
    """查询充值套餐列表"""
    query = db.query(RechargePackage)

    if keyword:
        query = query.filter(RechargePackage.package_name.contains(keyword))
    if enabled is not None:
        query = query.filter(RechargePackage.enabled == enabled)

    total = query.count()
    items = query.order_by(
        RechargePackage.sort_order.asc(),
        RechargePackage.id.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    return {"total": total, "items": items}


def create_recharge_package(db: Session, data: dict) -> RechargePackage:
    """创建充值套餐"""
    package = RechargePackage(**data)
    db.add(package)
    db.commit()
    db.refresh(package)

    app_logger.info(f"创建充值套餐: id={package.id}, name={package.package_name}")
    return package


def update_recharge_package(db: Session, package_id: int, data: dict) -> RechargePackage:
    """更新充值套餐"""
    package = db.query(RechargePackage).filter(RechargePackage.id == package_id).first()
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )

    for key, value in data.items():
        if value is not None:
            setattr(package, key, value)

    package.updated_at = now_beijing_naive()
    db.commit()
    db.refresh(package)

    app_logger.info(f"更新充值套餐: id={package_id}")
    return package


def delete_recharge_package(db: Session, package_id: int):
    """删除充值套餐"""
    package = db.query(RechargePackage).filter(RechargePackage.id == package_id).first()
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )

    db.delete(package)
    db.commit()

    app_logger.info(f"删除充值套餐: id={package_id}")


# ======================== 充值订单 ========================

def get_recharge_order_list(
    db: Session,
    user_id: Optional[int] = None,
    pay_status: Optional[str] = None,
    order_no: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> dict:
    """查询充值订单列表"""
    query = db.query(RechargeOrder)

    if user_id is not None:
        query = query.filter(RechargeOrder.user_id == user_id)
    if pay_status:
        query = query.filter(RechargeOrder.pay_status == pay_status)
    if order_no:
        query = query.filter(RechargeOrder.order_no == order_no)

    total = query.count()
    items = query.order_by(
        RechargeOrder.id.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    return {"total": total, "items": items}


def update_recharge_order_status(db: Session, order_id: int, pay_status: str) -> RechargeOrder:
    """更新充值订单状态"""
    order = db.query(RechargeOrder).filter(RechargeOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    valid_statuses = ["pending", "paid", "failed", "closed", "refunded"]
    if pay_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的状态值，允许: {', '.join(valid_statuses)}"
        )

    order.pay_status = pay_status
    if pay_status == "paid" and not order.paid_at:
        order.paid_at = now_beijing_naive()

    order.updated_at = now_beijing_naive()
    db.commit()
    db.refresh(order)

    app_logger.info(f"更新充值订单状态: order_id={order_id}, status={pay_status}")
    return order


# ======================== 用户积分账户 ========================

def get_point_account_list(
    db: Session,
    user_id: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> dict:
    """查询用户积分账户列表（关联用户名）"""
    query = db.query(
        UserPointAccount,
        User.username
    ).join(User, UserPointAccount.user_id == User.id)

    if user_id is not None:
        query = query.filter(UserPointAccount.user_id == user_id)
    if keyword:
        query = query.filter(User.username.contains(keyword))

    total = query.count()
    rows = query.order_by(
        UserPointAccount.id.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for account, username in rows:
        items.append({
            "id": account.id,
            "user_id": account.user_id,
            "username": username,
            "balance_points": account.balance_points,
            "frozen_points": account.frozen_points,
            "total_recharged_points": account.total_recharged_points,
            "total_consumed_points": account.total_consumed_points,
            "created_at": account.created_at,
            "updated_at": account.updated_at
        })

    return {"total": total, "items": items}


def admin_adjust_points(
    db: Session,
    user_id: int,
    points: int,
    remark: str
) -> UserPointAccount:
    """
    管理员手动调整用户积分

    Args:
        points: 正数增加积分，负数扣减积分
    """
    if points == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="调整积分不能为0"
        )

    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 查询积分账户（行锁）
    account = db.query(UserPointAccount).filter(
        UserPointAccount.user_id == user_id
    ).with_for_update().first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户积分账户不存在"
        )

    # 检查扣减时余额是否充足
    if points < 0 and account.balance_points + points < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"余额不足，当前余额: {account.balance_points}，需要扣减: {abs(points)}"
        )

    try:
        balance_before = account.balance_points

        # 调整积分
        if points > 0:
            account.balance_points += points
            account.total_recharged_points += points
        else:
            account.balance_points += points

        account.updated_at = now_beijing_naive()

        # 创建流水记录
        transaction_no = generate_transaction_no("ADJ")
        transaction = PointTransaction(
            transaction_no=transaction_no,
            user_id=user_id,
            type="admin_adjust",
            direction="income" if points > 0 else "expense",
            points=abs(points),
            balance_before=balance_before,
            balance_after=account.balance_points,
            frozen_before=account.frozen_points,
            frozen_after=account.frozen_points,
            remark=remark
        )
        db.add(transaction)

        db.commit()
        db.refresh(account)

        app_logger.info(
            f"管理员调整积分: user_id={user_id}, points={points}, "
            f"balance_before={balance_before}, balance_after={account.balance_points}"
        )

        return account

    except Exception as e:
        db.rollback()
        app_logger.error(f"管理员调整积分失败: {str(e)}")
        raise


# ======================== 积分流水 ========================

def get_point_transaction_list(
    db: Session,
    user_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> dict:
    """查询积分流水列表（关联用户名）"""
    query = db.query(
        PointTransaction,
        User.username
    ).outerjoin(User, PointTransaction.user_id == User.id)

    if user_id is not None:
        query = query.filter(PointTransaction.user_id == user_id)
    if transaction_type:
        query = query.filter(PointTransaction.type == transaction_type)

    total = query.count()
    rows = query.order_by(
        PointTransaction.id.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for transaction, username in rows:
        items.append({
            "id": transaction.id,
            "transaction_no": transaction.transaction_no,
            "user_id": transaction.user_id,
            "username": username,
            "type": transaction.type,
            "direction": transaction.direction,
            "points": transaction.points,
            "balance_before": transaction.balance_before,
            "balance_after": transaction.balance_after,
            "frozen_before": transaction.frozen_before,
            "frozen_after": transaction.frozen_after,
            "related_order_no": transaction.related_order_no,
            "related_task_id": transaction.related_task_id,
            "remark": transaction.remark,
            "created_at": transaction.created_at
        })

    return {"total": total, "items": items}


# ======================== 用户管理 ========================

def get_user_list(
    db: Session,
    keyword: Optional[str] = None,
    status_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> dict:
    """查询用户列表"""
    from app.models.user import User

    query = db.query(User)

    if keyword:
        query = query.filter(
            User.username.contains(keyword) |
            User.nickname.contains(keyword)
        )
    if status_filter:
        query = query.filter(User.status == status_filter)

    total = query.count()
    users = query.order_by(User.id.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {"total": total, "items": users}


def update_user_status(db: Session, user_id: int, new_status: str) -> "User":
    """
    更新用户状态（启用/禁用）

    第一版只做启用/禁用，不做删除用户，避免破坏历史数据。
    """
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    valid_statuses = ["normal", "disabled"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的状态值，允许: {', '.join(valid_statuses)}"
        )

    user.status = new_status
    user.updated_at = now_beijing_naive()
    db.commit()
    db.refresh(user)

    app_logger.info(f"更新用户状态: user_id={user_id}, status={new_status}")
    return user


# ======================== 生成任务管理 ========================

def get_generation_task_list(
    db: Session,
    user_id: Optional[int] = None,
    task_status: Optional[str] = None,
    task_id: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> dict:
    """查询生成任务列表（关联用户名）"""
    from app.models.generation_task import GenerationTask
    from app.models.user import User

    query = db.query(
        GenerationTask,
        User.username
    ).outerjoin(User, GenerationTask.user_id == User.id)

    if user_id is not None:
        query = query.filter(GenerationTask.user_id == user_id)
    if task_status:
        query = query.filter(GenerationTask.status == task_status)
    if task_id:
        query = query.filter(GenerationTask.task_id == task_id)
    if keyword:
        query = query.filter(
            GenerationTask.task_id.contains(keyword) |
            GenerationTask.model_key.contains(keyword) |
            GenerationTask.prompt.contains(keyword)
        )

    total = query.count()
    rows = query.order_by(
        GenerationTask.id.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for task, username in rows:
        items.append({
            "id": task.id,
            "task_id": task.task_id,
            "user_id": task.user_id,
            "username": username,
            "price_config_id": task.price_config_id,
            "model_key": task.model_key,
            "model_name": task.model_name,
            "capability_type": task.capability_type,
            "image_size": task.image_size,
            "image_count": task.image_count,
            "status": task.status,
            "frozen_points": task.frozen_points,
            "consumed_points": task.consumed_points,
            "refunded_points": task.refunded_points,
            "prompt": task.prompt,
            "error_message": task.error_message,
            "request_json": task.request_json,
            "provider_response_json": task.provider_response_json,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "finished_at": task.finished_at
        })

    return {"total": total, "items": items}
