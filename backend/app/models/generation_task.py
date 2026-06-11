"""
生成任务ORM模型
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, BigInteger, Integer, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.utils.timezone import now_beijing_naive

from app.db.base import Base


class GenerationTask(Base):
    """生成任务表"""

    __tablename__ = "generation_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    task_id: Mapped[str] = mapped_column(String(64), unique=True, comment="任务ID")
    user_id: Mapped[int] = mapped_column(BigInteger, comment="用户ID")

    price_config_id: Mapped[int] = mapped_column(BigInteger, comment="模型价格配置ID")

    model_key: Mapped[str] = mapped_column(String(128), comment="模型标识")
    model_name: Mapped[str] = mapped_column(String(128), comment="模型名称")
    provider_key: Mapped[Optional[str]] = mapped_column(String(64), comment="供应商标识")
    route_mode: Mapped[Optional[str]] = mapped_column(String(32), comment="路由模式")
    capability_type: Mapped[str] = mapped_column(String(32), comment="能力类型: image, video, text, audio")

    image_size: Mapped[Optional[str]] = mapped_column(String(32), comment="图片尺寸")
    image_count: Mapped[Optional[int]] = mapped_column(Integer, comment="图片数量")

    video_duration: Mapped[Optional[int]] = mapped_column(Integer, comment="视频时长")
    video_resolution: Mapped[Optional[str]] = mapped_column(String(32), comment="视频分辨率")

    status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        comment="状态: pending, running, success, failed"
    )

    frozen_points: Mapped[int] = mapped_column(BigInteger, default=0, comment="冻结积分")
    consumed_points: Mapped[int] = mapped_column(BigInteger, default=0, comment="实际消耗积分")
    refunded_points: Mapped[int] = mapped_column(BigInteger, default=0, comment="退回积分")

    prompt: Mapped[Optional[str]] = mapped_column(Text, comment="用户提示词")

    request_json: Mapped[Optional[dict]] = mapped_column(JSON, comment="请求参数")
    provider_response_json: Mapped[Optional[dict]] = mapped_column(JSON, comment="中转站返回原始数据")
    result_json: Mapped[Optional[dict]] = mapped_column(JSON, comment="最终返回给前端的数据")

    error_message: Mapped[Optional[str]] = mapped_column(Text, comment="错误信息")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_beijing_naive, comment="创建时间")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="开始执行时间")
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="完成时间")

    def __repr__(self):
        return f"<GenerationTask(task_id={self.task_id}, status={self.status})>"
