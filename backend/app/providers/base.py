"""
供应商基类
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class BaseProvider(ABC):
    """外部API供应商基类"""

    @abstractmethod
    def generate_image(
        self,
        model: str,
        prompt: str,
        size: str = "1024x1024",
        count: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成图片

        Args:
            model: 模型标识
            prompt: 提示词
            size: 图片尺寸
            count: 生成数量

        Returns:
            生成结果字典
        """
        pass

    def edit_image(
        self,
        model: str,
        prompt: str,
        image_urls: List[str],
        route_mode: Optional[str] = None,
        size: str = "1024x1024",
        count: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        编辑图片。默认不支持，由具体 provider 实现。
        """
        raise NotImplementedError("当前 provider 不支持图片编辑")

    @abstractmethod
    def generate_video(
        self,
        model: str,
        prompt: str,
        duration: int = 5,
        resolution: str = "720p",
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成视频

        Args:
            model: 模型标识
            prompt: 提示词
            duration: 视频时长（秒）
            resolution: 视频分辨率

        Returns:
            生成结果字典
        """
        pass
