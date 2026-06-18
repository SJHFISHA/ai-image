"""
任务查询相关路由
"""
from typing import Optional, List
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.generation import (
    TaskDetailResponse,
    TaskListResponse
)
from app.schemas.common import ApiResponse
from app.services import generation_service, conversation_service
from app.utils.timezone import now_beijing_naive
from app.providers.qiniu_provider import qiniu_provider

router = APIRouter(prefix="/tasks", tags=["任务"])

def resolve_task_image_urls(task) -> Optional[List[str]]:
    """
    Resolve task images for frontend display.

    Prefer assets[].key because private bucket needs temporary signed URLs.
    Fallback to result_json.images for old records.
    """
    if not task.result_json:
        return None

    assets = task.result_json.get("assets")
    if isinstance(assets, list):
        urls = []
        for asset in assets:
            key = asset.get("key") if isinstance(asset, dict) else None
            if key:
                urls.append(qiniu_provider.build_access_url(key))
        if urls:
            return urls

    images = task.result_json.get("images")
    if isinstance(images, list):
        return images

    return None


@router.get("/{task_id}", response_model=ApiResponse[TaskDetailResponse], summary="查询任务详情")
def get_task_detail(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    查询任务详情

    - task_id: 任务ID

    需要在请求头中携带: Authorization: Bearer <token>
    """
    task = generation_service.get_task_by_id(db, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    # 检查是否是当前用户的任务
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此任务"
        )

    if task.status == "running" and task.started_at:
        if now_beijing_naive() - task.started_at > timedelta(minutes=5):
            error_msg = "任务执行超时，请稍后重试"
            generation_service.settle_task_failed(db, task.task_id, error_msg)
            task = generation_service.get_task_by_id(db, task_id)

            message = conversation_service.get_message_by_task_id(db, task_id)
            if message:
                conversation_service.update_message_status(
                    db=db,
                    message_id=message.message_id,
                    status_val="failed",
                    content_text=error_msg,
                    metadata_json={"error": error_msg},
                )

    # 提取图片URL列表
    images = resolve_task_image_urls(task)

    response_data = TaskDetailResponse(
        task_id=task.task_id,
        status=task.status,
        model_key=task.model_key,
        model_name=task.model_name,
        capability_type=task.capability_type,
        image_size=task.image_size,
        image_count=task.image_count,
        aspect_ratio=task.aspect_ratio,
        prompt=task.prompt,
        frozen_points=task.frozen_points,
        consumed_points=task.consumed_points,
        refunded_points=task.refunded_points,
        error_message=task.error_message,
        images=images,
        created_at=task.created_at,
        finished_at=task.finished_at
    )

    return ApiResponse(
        code=0,
        message="success",
        data=response_data,
        success=True
    )


@router.get("", response_model=ApiResponse[TaskListResponse], summary="查询我的任务列表")
def get_my_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    查询我的任务列表

    - page: 页码（默认1）
    - page_size: 每页数量（默认20，最大100）

    需要在请求头中携带: Authorization: Bearer <token>
    """
    result = generation_service.get_user_tasks(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )

    items = []
    for task in result["items"]:
        # 提取图片URL列表
        images = resolve_task_image_urls(task)

        items.append(TaskDetailResponse(
            task_id=task.task_id,
            status=task.status,
            model_key=task.model_key,
            model_name=task.model_name,
            capability_type=task.capability_type,
            image_size=task.image_size,
            image_count=task.image_count,
            aspect_ratio=task.aspect_ratio,
            prompt=task.prompt,
            frozen_points=task.frozen_points,
            consumed_points=task.consumed_points,
            refunded_points=task.refunded_points,
            error_message=task.error_message,
            images=images,
            created_at=task.created_at,
            finished_at=task.finished_at
        ))

    response_data = TaskListResponse(
        total=result["total"],
        items=items
    )

    return ApiResponse(
        code=0,
        message="success",
        data=response_data,
        success=True
    )
