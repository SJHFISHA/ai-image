"""
认证相关路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RegisterResponse,
    UserInfo
)
from app.schemas.common import ApiResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=ApiResponse[RegisterResponse], summary="用户注册")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    用户注册

    - username: 用户名（2-64个字符，只能包含字母、数字、下划线）
    - password: 密码（6-128个字符）
    - confirm_password: 确认密码（必须与密码一致）
    """
    user = auth_service.register_user(
        db=db,
        username=request.username,
        password=request.password,
        confirm_password=request.confirm_password
    )

    response_data = RegisterResponse(
        message="注册成功",
        user=UserInfo(
            id=user.id,
            username=user.username,
            nickname=user.nickname,
            avatar_url=user.avatar_url
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
def get_me(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户信息

    需要在请求头中携带: Authorization: Bearer <token>
    """
    response_data = UserInfo(
        id=current_user.id,
        username=current_user.username,
        nickname=current_user.nickname,
        avatar_url=current_user.avatar_url
    )

    return ApiResponse(
        code=0,
        message="success",
        data=response_data,
        success=True
    )
