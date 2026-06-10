"""
生成任务业务逻辑模块
"""
from typing import Optional, List
from datetime import datetime
from app.utils.timezone import now_beijing_naive

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

    # 3. 在同一事务中冻结积分并创建任务
    try:
        # 冻结积分（不自动提交，由下方统一提交）
        point_service.freeze_points(
            db=db,
            user_id=user_id,
            points=price_config.points,
            related_task_id=task_id,
            remark=f"生图任务冻结积分 - {price_config.model_name}",
            auto_commit=False
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
            prompt=prompt,
            request_json={
                "price_config_id": price_config.id,
                "model": price_config.model_key,
                "prompt": prompt,
                "size": price_config.image_size,
                "count": price_config.image_count,
            }
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


def execute_image_generation(
    db: Session,
    task: GenerationTask,
    prompt: str,
    session_id: Optional[str] = None,
    assistant_message_id: Optional[str] = None,
) -> tuple[bool, Optional[str], Optional[dict]]:
    """
    执行生图任务

    Args:
        db: 数据库Session
        task: 任务对象
        prompt: 提示词
        session_id: 会话ID（用于写历史）
        assistant_message_id: assistant消息ID（用于更新历史）

    Returns:
        (success, error_message, result) 三元组
    """
    from app.providers.api_gateway_provider import api_gateway_provider
    from app.api.routes.image import extract_images_from_api_result
    from app.services import conversation_service

    try:
        # 更新任务状态为运行中，记录开始时间
        task.status = "running"
        task.started_at = now_beijing_naive()
        db.commit()

        app_logger.info(f"开始调用API生图: task_id={task.task_id}")

        # 调用 API 中转站
        api_result = api_gateway_provider.generate_image(
            model=task.model_key,
            prompt=prompt,
            size=task.image_size or "1024x1024",
            count=task.image_count or 1,
            quality="low",
            format="jpeg"
        )

        # 解析返回结果，提取图片 URL 或 base64
        images = extract_images_from_api_result(api_result)

        if not images:
            raise Exception(f"API未返回图片数据，原始返回: {api_result}")

        # 上传到七牛云，数据库只保存公开访问 URL
        from app.services import storage_service

        uploaded_assets = storage_service.upload_generated_media_list(
            values=images,
            user_id=task.user_id,
            task_id=task.task_id,
            media_type="image",
        )

        image_urls = [asset["url"] for asset in uploaded_assets]

        # 构建最终结果：只给前端和数据库保存可访问 URL
        result = {
            "images": image_urls,
            "assets": uploaded_assets,
        }

        # 成功结算
        settle_task_success(
            db,
            task.task_id,
            result,
            provider_response=sanitize_provider_response(api_result),
        )
        task.status = "success"

        # ========== 写入对话历史 ==========
        if session_id and assistant_message_id:
            # 更新 assistant 消息状态为 success
            conversation_service.update_message_status(
                db=db,
                message_id=assistant_message_id,
                status_val="success",
                content_text=f"生成了 {len(images)} 张图片",
                metadata_json={
                    "model": task.model_key,
                    "image_size": task.image_size,
                    "image_count": task.image_count,
                    "consumed_points": task.frozen_points,
                },
            )

            # 写入媒体资源记录
            for asset_info in uploaded_assets:
                conversation_service.create_media_asset(
                    db=db,
                    user_id=task.user_id,
                    url=asset_info["url"],
                    media_type="image",
                    session_id=session_id,
                    message_id=assistant_message_id,
                    task_id=task.task_id,
                    provider="qiniu",
                    bucket=asset_info.get("key"),
                    object_key=asset_info.get("key"),
                    mime_type=asset_info.get("mime_type"),
                )

            # 更新会话预览
            conversation_service.update_session_preview(
                db=db,
                session_id=session_id,
                preview=f"生成了 {len(images)} 张图片",
            )

        app_logger.info(f"生图成功: task_id={task.task_id}, images={len(images)}")

        return True, None, result

    except Exception as e:
        error_msg = str(e)
        app_logger.error(f"生图失败: task_id={task.task_id}, error={error_msg}")

        # 失败结算，退回积分
        settle_task_failed(db, task.task_id, error_msg)
        task.status = "failed"

        # ========== 更新对话历史（失败） ==========
        if session_id and assistant_message_id:
            from app.services import conversation_service
            conversation_service.update_message_status(
                db=db,
                message_id=assistant_message_id,
                status_val="failed",
                content_text=f"生成失败: {error_msg}",
                metadata_json={"error": error_msg},
            )
            conversation_service.update_session_preview(
                db=db,
                session_id=session_id,
                preview=f"图片生成失败: {error_msg[:80]}",
            )

        return False, error_msg, None


def execute_image_generation_by_task_id(
    task_id: str,
    prompt: str,
    session_id: Optional[str] = None,
    assistant_message_id: Optional[str] = None,
):
    """
    异步执行生图任务（供 BackgroundTasks 调用）

    注意：后台任务不能复用请求的 db Session，需自行创建和关闭。

    Args:
        task_id: 任务ID
        prompt: 提示词
        session_id: 会话ID（用于写历史）
        assistant_message_id: assistant消息ID（用于更新历史）
    """
    from app.db.database import SessionLocal

    db = SessionLocal()
    try:
        task = get_task_by_id(db, task_id)
        if task:
            execute_image_generation(
                db=db,
                task=task,
                prompt=prompt,
                session_id=session_id,
                assistant_message_id=assistant_message_id,
            )
        else:
            app_logger.error(f"异步执行生图任务失败: 任务不存在 task_id={task_id}")
    finally:
        db.close()

def sanitize_provider_response(response):
    """
    Remove large base64 payloads before saving provider_response_json.

    The generated media itself should be uploaded to Qiniu and saved as URL in
    result_json, not stored as raw base64 in provider_response_json.
    """
    if not isinstance(response, dict):
        return response

    def clean_value(value):
        if isinstance(value, dict):
            cleaned = {}
            for key, item in value.items():
                if key in {"b64_json", "image"} and isinstance(item, str) and len(item) > 500:
                    cleaned[key] = "[omitted_base64]"
                else:
                    cleaned[key] = clean_value(item)
            return cleaned

        if isinstance(value, list):
            return [clean_value(item) for item in value]

        if isinstance(value, str) and value.startswith("data:image/") and len(value) > 500:
            return "[omitted_data_url]"

        return value

    return clean_value(response)

def settle_task_success(
    db: Session,
    task_id: str,
    result: dict,
    provider_response: Optional[dict] = None
) -> GenerationTask:
    """
    任务成功结算

    Args:
        db: 数据库Session
        task_id: 任务ID
        result: 生成结果
        provider_response: 供应商原始响应

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
        # 扣除冻结积分（同一事务）
        point_service.consume_frozen_points(
            db=db,
            user_id=task.user_id,
            points=task.frozen_points,
            related_task_id=task_id,
            remark=f"生成任务成功扣除积分 - {task.model_name}",
            auto_commit=False
        )

        # 更新任务状态
        task.status = "success"
        task.consumed_points = task.frozen_points
        task.result_json = result
        task.provider_response_json = provider_response
        task.finished_at = now_beijing_naive()

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
        # 退回冻结积分（同一事务）
        point_service.unfreeze_points(
            db=db,
            user_id=task.user_id,
            points=task.frozen_points,
            related_task_id=task_id,
            remark=f"生成任务失败退回积分 - {task.model_name}",
            auto_commit=False
        )

        # 更新任务状态
        task.status = "failed"
        task.refunded_points = task.frozen_points
        task.error_message = error_message
        task.provider_response_json = {"error": error_message}
        task.finished_at = now_beijing_naive()

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
