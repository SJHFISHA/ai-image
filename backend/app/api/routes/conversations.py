"""
会话相关路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationItem,
    ConversationListResponse,
    ConversationDetailResponse,
    ConversationMessageResponse,
    MediaAssetResponse,
)
from app.services import conversation_service
from app.providers.qiniu_provider import qiniu_provider

router = APIRouter(prefix="/conversations", tags=["会话"])


@router.post("", response_model=ApiResponse[ConversationItem], summary="创建会话")
def create_conversation(
    request: ConversationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新会话"""
    conversation = conversation_service.create_session(
        db=db,
        user_id=current_user.id,
        session_type=request.session_type,
        title=request.title,
    )

    response_data = ConversationItem(
        session_id=conversation.session_id,
        title=conversation.title,
        session_type=conversation.session_type,
        last_message_preview=conversation.last_message_preview,
        last_message_at=conversation.last_message_at,
        created_at=conversation.created_at,
    )

    return ApiResponse(data=response_data)


@router.get("", response_model=ApiResponse[ConversationListResponse], summary="我的会话列表")
def get_my_conversations(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """查询我的会话列表"""
    try:
        result = conversation_service.get_user_sessions(
            db=db,
            user_id=current_user.id,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        from app.utils.logger import app_logger
        app_logger.error(f"查询会话列表失败: {str(e)}")
        # 如果表不存在等数据库问题，返回空列表而不是500
        return ApiResponse(data=ConversationListResponse(total=0, items=[]))

    items = [
        ConversationItem(
            session_id=s.session_id,
            title=s.title,
            session_type=s.session_type,
            last_message_preview=s.last_message_preview,
            last_message_at=s.last_message_at,
            created_at=s.created_at,
        )
        for s in result["items"]
    ]

    response_data = ConversationListResponse(total=result["total"], items=items)
    return ApiResponse(data=response_data)


@router.get("/{session_id}", response_model=ApiResponse[ConversationDetailResponse], summary="会话详情")
def get_conversation_detail(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取会话详情（含消息列表）"""
    conversation = conversation_service.get_session_detail(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
    )

    if not conversation:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    # 查询消息
    messages = conversation_service.get_messages_by_session(db, session_id)

    # 查询所有媒体资源，按 message_id 分组
    all_assets = conversation_service.get_assets_by_session(db, session_id)
    assets_by_message = {}
    for asset in all_assets:
        if asset.message_id:
            if asset.message_id not in assets_by_message:
                assets_by_message[asset.message_id] = []
            assets_by_message[asset.message_id].append(
                MediaAssetResponse(
                    asset_id=asset.asset_id,
                    media_type=asset.media_type,
                    url=qiniu_provider.build_access_url(asset.object_key) if asset.object_key else asset.url,
                    mime_type=asset.mime_type,
                    file_size=asset.file_size,
                    width=asset.width,
                    height=asset.height,
                )
            )

    message_list = [
        ConversationMessageResponse(
            message_id=m.message_id,
            role=m.role,
            content_type=m.content_type,
            content_text=m.content_text,
            task_id=m.task_id,
            status=m.status,
            metadata_json=m.metadata_json,
            assets=assets_by_message.get(m.message_id, []),
            created_at=m.created_at,
        )
        for m in messages
    ]

    response_data = ConversationDetailResponse(
        session_id=conversation.session_id,
        title=conversation.title,
        session_type=conversation.session_type,
        messages=message_list,
    )

    return ApiResponse(data=response_data)


@router.delete("/{session_id}", summary="删除会话")
def delete_conversation(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """软删除会话"""
    success = conversation_service.delete_session(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
    )

    if not success:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    return ApiResponse(message="删除成功")
