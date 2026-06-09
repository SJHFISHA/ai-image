"""
ID生成器 - 用于生成订单号、任务ID、流水号等
"""
import uuid
import time
from datetime import datetime


def generate_order_no(prefix: str = "ORD") -> str:
    """
    生成充值订单号

    格式: ORD + 时间戳 + 随机数
    示例: ORD20260608123456ABC123
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = uuid.uuid4().hex[:8].upper()
    return f"{prefix}{timestamp}{random_suffix}"


def generate_task_id(prefix: str = "IMG") -> str:
    """
    生成生图任务ID

    格式: IMG + 时间戳 + 随机数
    示例: IMG20260608123456ABC123
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = uuid.uuid4().hex[:8].upper()
    return f"{prefix}{timestamp}{random_suffix}"


def generate_transaction_no(prefix: str = "TXN") -> str:
    """
    生成积分流水号

    格式: TXN + 时间戳 + 随机数
    示例: TXN20260608123456ABC123
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = uuid.uuid4().hex[:8].upper()
    return f"{prefix}{timestamp}{random_suffix}"


def generate_video_task_id() -> str:
    """
    生成视频任务ID

    格式: VID + 时间戳 + 随机数
    """
    return generate_task_id(prefix="VID")


def generate_audio_task_id() -> str:
    """
    生成音频任务ID

    格式: AUD + 时间戳 + 随机数
    """
    return generate_task_id(prefix="AUD")
