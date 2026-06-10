"""
时区工具模块 - 统一使用北京时间
"""
from datetime import datetime, timezone, timedelta

# 北京时间 UTC+8
BEIJING_TZ = timezone(timedelta(hours=8))


def now_beijing() -> datetime:
    """
    获取当前北京时间

    Returns:
        当前北京时间（带时区信息）
    """
    return datetime.now(BEIJING_TZ)


def now_beijing_naive() -> datetime:
    """
    获取当前北京时间（不带时区信息，用于数据库存储）

    Returns:
        当前北京时间（naive datetime）
    """
    return datetime.now(BEIJING_TZ).replace(tzinfo=None)
