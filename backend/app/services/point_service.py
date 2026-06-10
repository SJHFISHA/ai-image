"""
积分业务逻辑模块
"""
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.models.user import User
from app.models.point import UserPointAccount, PointTransaction
from app.utils.id_generator import generate_transaction_no
from app.utils.logger import app_logger


def get_point_account(db: Session, user_id: int) -> Optional[UserPointAccount]:
    """
    获取用户积分账户

    Args:
        db: 数据库Session
        user_id: 用户ID

    Returns:
        积分账户对象
    """
    return db.query(UserPointAccount).filter(UserPointAccount.user_id == user_id).first()


def get_point_balance(db: Session, user_id: int) -> dict:
    """
    查询用户积分余额

    Args:
        db: 数据库Session
        user_id: 用户ID

    Returns:
        积分余额信息字典
    """
    account = get_point_account(db, user_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="积分账户不存在"
        )

    return {
        "balance_points": account.balance_points,
        "frozen_points": account.frozen_points,
        "total_recharged_points": account.total_recharged_points,
        "total_consumed_points": account.total_consumed_points
    }


def add_points(
    db: Session,
    user_id: int,
    points: int,
    transaction_type: str = "recharge",
    related_order_no: Optional[str] = None,
    remark: Optional[str] = None,
    auto_commit: bool = True
) -> PointTransaction:
    """
    增加积分（充值到账）

    Args:
        db: 数据库Session
        user_id: 用户ID
        points: 增加的积分数量
        transaction_type: 流水类型
        related_order_no: 关联订单号
        remark: 备注
        auto_commit: 是否自动提交事务，默认True。设为False时由调用方控制事务提交。

    Returns:
        积分流水记录
    """
    # 查询积分账户并锁定
    account = db.query(UserPointAccount).filter(
        UserPointAccount.user_id == user_id
    ).with_for_update().first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="积分账户不存在"
        )

    # 记录变动前的状态
    balance_before = account.balance_points
    frozen_before = account.frozen_points

    # 增加可用积分
    account.balance_points += points
    account.total_recharged_points += points

    # 创建积分流水
    transaction_no = generate_transaction_no()
    transaction = PointTransaction(
        transaction_no=transaction_no,
        user_id=user_id,
        type=transaction_type,
        direction="income",
        points=points,
        balance_before=balance_before,
        balance_after=account.balance_points,
        frozen_before=frozen_before,
        frozen_after=account.frozen_points,
        related_order_no=related_order_no,
        remark=remark
    )
    db.add(transaction)

    if auto_commit:
        db.commit()

    app_logger.info(
        f"积分增加: user_id={user_id}, points={points}, "
        f"balance_before={balance_before}, balance_after={account.balance_points}"
    )

    return transaction


def freeze_points(
    db: Session,
    user_id: int,
    points: int,
    related_task_id: Optional[str] = None,
    remark: Optional[str] = None,
    auto_commit: bool = True
) -> PointTransaction:
    """
    冻结积分（创建任务时）

    Args:
        db: 数据库Session
        user_id: 用户ID
        points: 冻结的积分数量
        related_task_id: 关联任务ID
        remark: 备注
        auto_commit: 是否自动提交事务，默认True。设为False时由调用方控制事务提交。

    Returns:
        积分流水记录
    """
    # 查询积分账户并锁定
    account = db.query(UserPointAccount).filter(
        UserPointAccount.user_id == user_id
    ).with_for_update().first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="积分账户不存在"
        )

    # 检查可用积分是否足够
    if account.balance_points < points:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="积分不足"
        )

    # 记录变动前的状态
    balance_before = account.balance_points
    frozen_before = account.frozen_points

    # 减少可用积分，增加冻结积分
    account.balance_points -= points
    account.frozen_points += points

    # 创建积分流水
    transaction_no = generate_transaction_no()
    transaction = PointTransaction(
        transaction_no=transaction_no,
        user_id=user_id,
        type="freeze",
        direction="freeze",
        points=points,
        balance_before=balance_before,
        balance_after=account.balance_points,
        frozen_before=frozen_before,
        frozen_after=account.frozen_points,
        related_task_id=related_task_id,
        remark=remark or "创建任务冻结积分"
    )
    db.add(transaction)

    if auto_commit:
        db.commit()

    app_logger.info(
        f"积分冻结: user_id={user_id}, points={points}, "
        f"balance_after={account.balance_points}, frozen_after={account.frozen_points}"
    )

    return transaction


def consume_frozen_points(
    db: Session,
    user_id: int,
    points: int,
    related_task_id: Optional[str] = None,
    remark: Optional[str] = None,
    auto_commit: bool = True
) -> PointTransaction:
    """
    扣除冻结积分（任务成功时）

    Args:
        db: 数据库Session
        user_id: 用户ID
        points: 扣除的积分数量
        related_task_id: 关联任务ID
        remark: 备注
        auto_commit: 是否自动提交事务，默认True。设为False时由调用方控制事务提交。

    Returns:
        积分流水记录
    """
    # 查询积分账户并锁定
    account = db.query(UserPointAccount).filter(
        UserPointAccount.user_id == user_id
    ).with_for_update().first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="积分账户不存在"
        )

    # 检查冻结积分是否足够
    if account.frozen_points < points:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="冻结积分不足"
        )

    # 记录变动前的状态
    balance_before = account.balance_points
    frozen_before = account.frozen_points

    # 减少冻结积分，增加累计消费
    account.frozen_points -= points
    account.total_consumed_points += points

    # 创建积分流水
    transaction_no = generate_transaction_no()
    transaction = PointTransaction(
        transaction_no=transaction_no,
        user_id=user_id,
        type="consume",
        direction="expense",
        points=points,
        balance_before=balance_before,
        balance_after=account.balance_points,
        frozen_before=frozen_before,
        frozen_after=account.frozen_points,
        related_task_id=related_task_id,
        remark=remark or "生成任务成功扣除积分"
    )
    db.add(transaction)

    if auto_commit:
        db.commit()

    app_logger.info(
        f"积分扣除: user_id={user_id}, points={points}, "
        f"frozen_after={account.frozen_points}, consumed_after={account.total_consumed_points}"
    )

    return transaction


def unfreeze_points(
    db: Session,
    user_id: int,
    points: int,
    related_task_id: Optional[str] = None,
    remark: Optional[str] = None,
    auto_commit: bool = True
) -> PointTransaction:
    """
    解冻积分（任务失败时）

    Args:
        db: 数据库Session
        user_id: 用户ID
        points: 解冻的积分数量
        related_task_id: 关联任务ID
        remark: 备注
        auto_commit: 是否自动提交事务，默认True。设为False时由调用方控制事务提交。

    Returns:
        积分流水记录
    """
    # 查询积分账户并锁定
    account = db.query(UserPointAccount).filter(
        UserPointAccount.user_id == user_id
    ).with_for_update().first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="积分账户不存在"
        )

    # 检查冻结积分是否足够
    if account.frozen_points < points:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="冻结积分不足"
        )

    # 记录变动前的状态
    balance_before = account.balance_points
    frozen_before = account.frozen_points

    # 减少冻结积分，增加可用积分
    account.frozen_points -= points
    account.balance_points += points

    # 创建积分流水
    transaction_no = generate_transaction_no()
    transaction = PointTransaction(
        transaction_no=transaction_no,
        user_id=user_id,
        type="unfreeze",
        direction="unfreeze",
        points=points,
        balance_before=balance_before,
        balance_after=account.balance_points,
        frozen_before=frozen_before,
        frozen_after=account.frozen_points,
        related_task_id=related_task_id,
        remark=remark or "生成任务失败退回积分"
    )
    db.add(transaction)

    if auto_commit:
        db.commit()

    app_logger.info(
        f"积分解冻: user_id={user_id}, points={points}, "
        f"balance_after={account.balance_points}, frozen_after={account.frozen_points}"
    )

    return transaction


def get_point_transactions(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20
) -> dict:
    """
    查询积分流水列表

    Args:
        db: 数据库Session
        user_id: 用户ID
        page: 页码
        page_size: 每页数量

    Returns:
        包含总数和流水列表的字典
    """
    # 查询总数
    total = db.query(PointTransaction).filter(
        PointTransaction.user_id == user_id
    ).count()

    # 查询列表
    transactions = db.query(PointTransaction).filter(
        PointTransaction.user_id == user_id
    ).order_by(
        PointTransaction.created_at.desc()
    ).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "total": total,
        "items": transactions
    }
