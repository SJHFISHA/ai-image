"""
通用校验工具模块
"""
import re
from typing import Optional


def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """
    校验用户名是否合法

    规则:
    - 长度2-64
    - 只能包含字母、数字、下划线

    Returns:
        (是否合法, 错误信息)
    """
    if not username or len(username) < 2:
        return False, "用户名长度不能少于2个字符"

    if len(username) > 64:
        return False, "用户名长度不能超过64个字符"

    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "用户名只能包含字母、数字和下划线"

    return True, None


def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    校验密码是否合法

    规则:
    - 长度6-128

    Returns:
        (是否合法, 错误信息)
    """
    if not password or len(password) < 6:
        return False, "密码长度不能少于6个字符"

    if len(password) > 128:
        return False, "密码长度不能超过128个字符"

    return True, None


def validate_email(email: str) -> tuple[bool, Optional[str]]:
    """
    校验邮箱格式是否合法

    Returns:
        (是否合法, 错误信息)
    """
    if not email:
        return True, None  # 邮箱是可选的

    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return False, "邮箱格式不正确"

    return True, None


def validate_phone(phone: str) -> tuple[bool, Optional[str]]:
    """
    校验手机号格式是否合法

    Returns:
        (是否合法, 错误信息)
    """
    if not phone:
        return True, None  # 手机号是可选的

    phone_regex = r'^1[3-9]\d{9}$'
    if not re.match(phone_regex, phone):
        return False, "手机号格式不正确"

    return True, None
