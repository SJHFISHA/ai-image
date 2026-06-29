"""
认证相关路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RegisterResponse,
    UserInfo,
    AvatarUploadResponse,
    UseInviteCodeRequest,
    UseInviteCodeResponse
)
from app.schemas.common import ApiResponse
from app.services import auth_service
from app.services.point_service import get_point_balance
from app.services.invitation_service import get_invitation_stats, use_invite_code as use_invite_code_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=ApiResponse[RegisterResponse], summary="用户注册")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    用户注册

    - username: 用户名（2-64个字符，只能包含字母、数字、下划线）
    - password: 密码（6-128个字符）
    - confirm_password: 确认密码（必须与密码一致）
    - invite_code: 邀请码（可选）
    """
    user = auth_service.register_user(
        db=db,
        username=request.username,
        password=request.password,
        confirm_password=request.confirm_password,
        invite_code=request.invite_code
    )

    # 获取积分余额（如果填了邀请码，会有50积分）
    point_balance = get_point_balance(db, user.id)

    # 获取邀请统计
    invitation_stats = get_invitation_stats(db, user.id)

    response_data = RegisterResponse(
        message="注册成功",
        user=UserInfo(
            id=user.id,
            username=user.username,
            nickname=user.nickname,
            avatar_url=auth_service.get_avatar_url(user.avatar_url),
            available_points=point_balance.get("balance_points", 0),
            invite_code=user.invite_code,
            invite_reward_count=invitation_stats.get("invite_reward_count", 0),
            invite_reward_remaining=invitation_stats.get("invite_reward_remaining", 5),
            used_invite_count=invitation_stats.get("used_invite_count", 0),
            used_invite_remaining=invitation_stats.get("used_invite_remaining", 5)
        )
    )

    return ApiResponse(
        code=0,
        message="注册成功",
        data=response_data,
        success=True
    )


@router.post("/login", response_model=ApiResponse[TokenResponse], summary="用户登录")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录

    - username: 用户名
    - password: 密码

    返回JWT token和用户信息
    """
    result = auth_service.login_user(
        db=db,
        username=request.username,
        password=request.password
    )

    response_data = TokenResponse(**result)

    return ApiResponse(
        code=0,
        message="登录成功",
        data=response_data,
        success=True
    )


@router.get("/me", response_model=ApiResponse[UserInfo], summary="获取当前用户信息")
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    获取当前登录用户信息

    需要在请求头中携带: Authorization: Bearer <token>
    """
    point_balance = get_point_balance(db, current_user.id)
    invitation_stats = get_invitation_stats(db, current_user.id)

    response_data = UserInfo(
        id=current_user.id,
        username=current_user.username,
        nickname=current_user.nickname,
        avatar_url=auth_service.get_avatar_url(current_user.avatar_url),
        available_points=point_balance.get("balance_points", 0),
        invite_code=current_user.invite_code,
        invite_reward_count=invitation_stats.get("invite_reward_count", 0),
        invite_reward_remaining=invitation_stats.get("invite_reward_remaining", 5),
        used_invite_count=invitation_stats.get("used_invite_count", 0),
        used_invite_remaining=invitation_stats.get("used_invite_remaining", 5)
    )

    return ApiResponse(
        code=0,
        message="success",
        data=response_data,
        success=True
    )


@router.post("/use-invite-code", response_model=ApiResponse[UseInviteCodeResponse], summary="使用邀请码")
def use_invite_code(
    request: UseInviteCodeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    使用邀请码（登录后填写）

    - invite_code: 邀请码
    - 需要在请求头中携带: Authorization: Bearer <token>
    """
    invitation_record = use_invite_code_service(
        db=db,
        invitee_user_id=current_user.id,
        invite_code=request.invite_code
    )

    # 获取最新的邀请统计
    invitation_stats = get_invitation_stats(db, current_user.id)

    response_data = UseInviteCodeResponse(
        reward_points=invitation_record.reward_points,
        used_invite_count=invitation_stats.get("used_invite_count", 0),
        used_invite_remaining=invitation_stats.get("used_invite_remaining", 4)
    )

    return ApiResponse(
        code=0,
        message="邀请码使用成功，双方各获得50积分",
        data=response_data,
        success=True
    )


@router.post("/avatar", response_model=ApiResponse[AvatarUploadResponse], summary="上传用户头像")
async def upload_avatar(
    file: UploadFile = File(..., description="头像图片文件"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传用户头像

    - 支持格式：JPG、PNG、WebP、GIF
    - 最大大小：2MB
    - 需要在请求头中携带: Authorization: Bearer <token>
    """
    avatar_url = await auth_service.upload_avatar(
        db=db,
        user_id=current_user.id,
        file=file
    )

    response_data = AvatarUploadResponse(avatar_url=avatar_url)

    return ApiResponse(
        code=0,
        message="头像上传成功",
        data=response_data,
        success=True
    )
