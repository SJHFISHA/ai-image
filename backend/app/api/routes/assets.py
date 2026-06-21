from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.conversation import MediaAsset
from app.models.generation_task import GenerationTask
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.generation import AssetItemResponse, AssetListResponse
from app.providers.qiniu_provider import qiniu_provider

router = APIRouter(prefix="/assets", tags=["资产"])


@router.get("", response_model=ApiResponse[AssetListResponse], summary="查询我的资产")
def get_assets(
    type: Optional[str] = Query(None, description="资产类型: image, video, audio"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(80, ge=1, le=200, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed_types = ["image", "video", "audio"]

    if type and type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的资产类型"
        )

    query = db.query(MediaAsset, GenerationTask).outerjoin(
        GenerationTask,
        MediaAsset.task_id == GenerationTask.task_id
    ).filter(
        MediaAsset.user_id == current_user.id,
        MediaAsset.media_type.in_(allowed_types),
    )

    if type:
        query = query.filter(MediaAsset.media_type == type)

    total = query.count()

    rows = query.order_by(
        MediaAsset.created_at.desc(),
        MediaAsset.id.desc(),
    ).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    items = []
    for asset, task in rows:
        asset_url = qiniu_provider.build_access_url(asset.object_key) if asset.object_key else asset.url

        items.append(AssetItemResponse(
            id=asset.id,
            asset_id=asset.asset_id,
            task_id=asset.task_id or "",
            type=asset.media_type,
            url=asset_url,
            cover_url=asset_url if asset.media_type == "image" else None,
            title=task.prompt if task else None,
            prompt=task.prompt if task else None,
            model_name=task.model_name if task else None,
            created_at=asset.created_at,
        ))

    return ApiResponse(
        code=0,
        message="success",
        data=AssetListResponse(
            total=total,
            items=items,
        ),
        success=True,
    )