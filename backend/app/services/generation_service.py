"""
生成任务业务逻辑模块
"""
from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.generation_task import GenerationTask
from app.models.model_price import ModelPriceConfig
from app.services import point_service, model_price_service
from app.utils.id_generator import generate_task_id
from app.utils.logger import app_logger


def create_image_task(
    db: Session,
    user_id: int,
    price_config_id: int,
    prompt: str
) -> GenerationTask:
    """
    创建生图任务

    Args:
        db: 数据库Session
        user_id: 用户ID
        price_config_id: 模型价格配置ID
        prompt: 提示词

    Returns:
        创建的任务对象

    Raises:
        HTTPException: 参数错误或积分不足时抛出异常
    """
    # 1. 查询并验证模型价格配置
    price_config = model_price_service.validate_model_price_config(
        db, price_config_id, capability_type="image"
    )

    # 2. 生成任务ID
    task_id = generate_task_id("IMG")

    # 3. 在事务中冻结积分并创建任务
    try:
        # 冻结积分
        point_service.freeze_points(
            db=db,
            user_id=user_id,
            points=price_config.points,
            related_task_id=task_id,
            remark=f"生图任务冻结积分 - {price_config.model_name}"
        )

        # 创建任务记录
        task = GenerationTask(
            task_id=task_id,
            user_id=user_id,
            price_config_id=price_config.id,
            model_key=price_config.model_key,
            model_name=price_config.model_name,
            capability_type="image",
            image_size=price_config.image_size,
            image_count=price_config.image_count,
            status="pending",
            frozen_points=price_config.points,
            prompt=prompt
        )
        db.add(task)
        db.commit()

        app_logger.info(
            f"生图任务创建成功: task_id={task_id}, user_id={user_id}, "
            f"model={price_config.model_key}, points={price_config.points}"
        )

        return task

    except Exception as e:
        db.rollback()
        app_logger.error(f"生图任务创建失败: {str(e)}")
        raise


def mock_generate_image(task_id: str) -> dict:
    """
    Mock生图函数（用于测试）

    Args:
        task_id: 任务ID

    Returns:
        生成结果字典
    """
    # 模拟生成成功
    return {
        "images": [
            "https://example.com/test-image-1.png",
            "https://example.com/test-image-2.png"
        ]
    }


def settle_task_success(
    db: Session,
    task_id: str,
    result: dict
) -> GenerationTask:
    """
    任务成功结算

    Args:
        db: 数据库Session
        task_id: 任务ID
        result: 生成结果

    Returns:
        更新后的任务对象
    """
    # 查询任务
    task = db.query(GenerationTask).filter(
        GenerationTask.task_id == task_id
    ).with_for_update().first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    # 检查任务状态，防止重复结算
    if task.status == "success":
        app_logger.warning(f"任务已成功，跳过重复结算: task_id={task_id}")
        return task

    if task.status in ["failed"]:
        app_logger.warning(f"任务已失败，无法结算为成功: task_id={task_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务已失败，无法结算"
        )

    try:
        # 扣除冻结积分
        point_service.consume_frozen_points(
            db=db,
            user_id=task.user_id,
            points=task.frozen_points,
            related_task_id=task_id,
            remark=f"生成任务成功扣除积分 - {task.model_name}"
        )

        # 更新任务状态
        task.status = "success"
        task.consumed_points = task.frozen_points
        task.result_json = result
        task.finished_at = datetime.utcnow()

        db.commit()

        app_logger.info(
            f"任务结算成功: task_id={task_id}, consumed_points={task.frozen_points}"
        )

        return task

    except Exception as e:
        db.rollback()
        app_logger.error(f"任务结算失败: {str(e)}")
        raise


def settle_task_failed(
    db: Session,
    task_id: str,
    error_message: str
) -> GenerationTask:
    """
    任务失败结算（退回积分）

    Args:
        db: 数据库Session
        task_id: 任务ID
        error_message: 错误信息

    Returns:
        更新后的任务对象
    """
    # 查询任务
    task = db.query(GenerationTask).filter(
        GenerationTask.task_id == task_id
    ).with_for_update().first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    # 检查任务状态，防止重复结算
    if task.status in ["success", "failed"]:
        app_logger.warning(f"任务已结算，跳过重复操作: task_id={task_id}, status={task.status}")
        return task

    try:
        # 退回冻结积分
        point_service.unfreeze_points(
            db=db,
            user_id=task.user_id,
            points=task.frozen_points,
            related_task_id=task_id,
            remark=f"生成任务失败退回积分 - {task.model_name}"
        )

        # 更新任务状态
        task.status = "failed"
        task.refunded_points = task.frozen_points
        task.error_message = error_message
        task.finished_at = datetime.utcnow()

        db.commit()

        app_logger.info(
            f"任务失败结算: task_id={task_id}, refunded_points={task.frozen_points}"
        )

        return task

    except Exception as e:
        db.rollback()
        app_logger.error(f"任务失败结算失败: {str(e)}")
        raise


def get_task_by_id(db: Session, task_id: str) -> Optional[GenerationTask]:
    """
    根据任务ID查询任务

    Args:
        db: 数据库Session
        task_id: 任务ID

    Returns:
        任务对象
    """
    return db.query(GenerationTask).filter(
        GenerationTask.task_id == task_id
    ).first()


def get_user_tasks(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20
) -> dict:
    """
    查询用户任务列表

    Args:
        db: 数据库Session
        user_id: 用户ID
        page: 页码
        page_size: 每页数量

    Returns:
        包含总数和任务列表的字典
    """
    # 查询总数
    total = db.query(GenerationTask).filter(
        GenerationTask.user_id == user_id
    ).count()

    # 查询列表
    tasks = db.query(GenerationTask).filter(
        GenerationTask.user_id == user_id
    ).order_by(
        GenerationTask.created_at.desc()
    ).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "total": total,
        "items": tasks
    }
