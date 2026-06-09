"""
认证相关请求和响应模型
"""
from pydantic import BaseModel, Field
from typing import Optional


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=2, max_length=64, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    confirm_password: str = Field(..., min_length=6, max_length=128, description="确认密码")


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserInfo(BaseModel):
    """用户信息"""
    id: int = Field(..., description="用户ID")
    username: Optional[str] = Field(None, description="用户名")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """登录成功响应"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="Bearer", description="令牌类型")
    user: UserInfo = Field(..., description="用户信息")


class RegisterResponse(BaseModel):
    """注册成功响应"""
    message: str = Field(default="注册成功", description="提示信息")
    user: UserInfo = Field(..., description="用户信息")
