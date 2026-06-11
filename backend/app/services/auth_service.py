"""
认证业务逻辑模块
"""
from typing import Optional
from datetime import datetime
from app.utils.timezone import now_beijing_naive

from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile

from app.models.user import User
from app.models.point import UserPointAccount
from app.core.security import hash_password, verify_password, create_access_token
from app.utils.validators import validate_username, validate_password
from app.utils.logger import app_logger
from app.providers.qiniu_provider import qiniu_provider


def register_user(
    db: Session,
    username: str,
    password: str,
    confirm_password: str
) -> User:
    """
    用户注册

    Args:
        db: 数据库Session
        username: 用户名
        password: 密码
        confirm_password: 确认密码

    Returns:
        创建的用户对象

    Raises:
        HTTPException: 参数校验失败或用户名已存在时抛出异常
    """
    # 校验用户名
    is_valid, error_msg = validate_username(username)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # 校验密码
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # 校验两次密码是否一致
    if password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="两次输入的密码不一致"
        )

    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    try:
        # 开启事务
        # 创建用户
        user = User(
            username=username,
            password_hash=hash_password(password),
            nickname=username,
            status="normal"
        )
        db.add(user)
        db.flush()  # 获取user.id

        # 创建积分账户
        point_account = UserPointAccount(
            user_id=user.id,
            balance_points=0,
            frozen_points=0,
            total_recharged_points=0,
            total_consumed_points=0
        )
        db.add(point_account)

        # 提交事务
        db.commit()

        app_logger.info(f"用户注册成功: username={username}, user_id={user.id}")
        return user

    except Exception as e:
        db.rollback()
        app_logger.error(f"用户注册失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )


def login_user(
    db: Session,
    username: str,
    password: str
) -> dict:
    """
    用户登录

    Args:
        db: 数据库Session
        username: 用户名
        password: 密码

    Returns:
        包含access_token和用户信息的字典

    Raises:
        HTTPException: 用户名或密码错误时抛出异常
    """
    # 查询用户
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 检查用户状态
    if user.status != "normal":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )

    # 校验密码
    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 更新最后登录时间
    user.last_login_at = now_beijing_naive()
    db.commit()

    # 生成JWT token
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )

    app_logger.info(f"用户登录成功: username={username}, user_id={user.id}")

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "avatar_url": get_avatar_url(user.avatar_url)
        }
    }


def get_user_info(db: Session, user_id: int) -> Optional[User]:
    """
    获取用户信息

    Args:
        db: 数据库Session
        user_id: 用户ID

    Returns:
        用户对象，如果不存在返回None
    """
    return db.query(User).filter(User.id == user_id).first()


def get_avatar_url(avatar_key: Optional[str]) -> Optional[str]:
    """
    将头像key转换为可访问的签名URL

    Args:
        avatar_key: 头像在七牛云的object key

    Returns:
        签名URL，如果key为空返回None
    """
    if not avatar_key:
        return None
    return qiniu_provider.build_access_url(avatar_key)


# 允许的头像文件类型
ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
# 最大头像文件大小（50MB）
MAX_AVATAR_SIZE = 50 * 1024 * 1024


async def upload_avatar(db: Session, user_id: int, file: UploadFile) -> str:
    """
    上传用户头像到七牛云

    Args:
        db: 数据库Session
        user_id: 用户ID
        file: 上传的文件

    Returns:
        头像访问URL

    Raises:
        HTTPException: 文件校验失败或上传失败时抛出异常
    """
    # 校验文件类型
    if file.content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的图片格式，仅支持 JPG、PNG、WebP、GIF"
        )

    # 读取文件内容并校验大小
    content = await file.read()
    if len(content) > MAX_AVATAR_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="图片大小不能超过2MB"
        )

    # 确定文件后缀
    suffix_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif"
    }
    suffix = suffix_map.get(file.content_type, ".png")

    # 生成object key
    timestamp = int(datetime.now().timestamp() * 1000)
    object_key = f"avatars/user_{user_id}/{timestamp}{suffix}"

    try:
        # 上传到七牛云
        result = qiniu_provider.upload_bytes(content, object_key, suffix)

        # 更新数据库
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        user.avatar_url = object_key
        db.commit()

        # 返回签名URL（bucket是私有的，需要签名才能访问）
        access_url = qiniu_provider.build_access_url(object_key)
        app_logger.info(f"用户头像上传成功: user_id={user_id}, key={object_key}")
        return access_url

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        app_logger.error(f"用户头像上传失败: user_id={user_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="头像上传失败，请稍后重试"
        )
