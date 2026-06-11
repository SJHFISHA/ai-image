"""
API中转站调用模块
"""
import requests
from typing import Dict, Any, Optional

from app.core.config import settings
from app.providers.base import BaseProvider
from app.utils.logger import app_logger


# 路由模式后缀映射
ROUTE_SUFFIX_MAP = {
    "price": ":floor",
    "speed": ":nitro",
    "success_rate": ":stable",
}


class ApiGatewayProvider(BaseProvider):
    """API中转站调用实现"""

    def __init__(self):
        self.base_url = settings.API_GATEWAY_BASE_URL
        self.api_key = settings.API_GATEWAY_API_KEY

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def _apply_route_suffix(self, model: str, route_mode: Optional[str] = None) -> str:
        """
        根据路由模式为模型名添加后缀

        Args:
            model: 原始模型标识
            route_mode: 路由模式 (price, speed, success_rate)

        Returns:
            添加后缀后的模型标识
        """
        if not route_mode:
            return model

        suffix = ROUTE_SUFFIX_MAP.get(route_mode)
        if not suffix:
            return model

        # 如果已经有路由后缀，不再添加
        if model.endswith(":floor") or model.endswith(":nitro") or model.endswith(":stable"):
            return model

        return f"{model}{suffix}"

    def generate_image(
        self,
        model: str,
        prompt: str,
        size: str = "1024x1024",
        count: int = 1,
        quality: str = "low",
        format: str = "jpeg",
        route_mode: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用API中转站生成图片

        Args:
            model: 模型标识，例如 gpt-image-2
            prompt: 提示词
            size: 图片尺寸，例如 1024x1024, 1024x1536, 1536x1024
            count: 生成数量
            quality: 图片质量 (low, medium, high, auto)
            format: 图片格式 (jpeg, png)
            route_mode: 路由模式 (price, speed, success_rate)

        Returns:
            API返回的原始响应

        Raises:
            Exception: API调用失败时抛出异常
        """
        url = f"{self.base_url}/v1/images/generations"

        # 应用路由后缀
        routed_model = self._apply_route_suffix(model, route_mode)

        payload = {
            "model": routed_model,
            "prompt": prompt,
            "n": count,
            "size": size,
            "quality": quality,
            "format": format
        }

        # 合并额外参数（排除已处理的参数）
        kwargs.pop('route_mode', None)
        payload.update(kwargs)

        app_logger.info(f"调用API中转站生图: model={routed_model}, size={size}, count={count}, route_mode={route_mode}")

        try:
            session = requests.Session()
            session.trust_env = False

            response = session.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=180
            )

            if response.status_code >= 400:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                app_logger.error(error_msg)
                raise Exception(error_msg)

            result = response.json()

            app_logger.info(f"API中转站生图成功: model={routed_model}")
            return result

        except requests.RequestException as e:
            error_msg = f"API请求错误: {str(e)}"
            app_logger.error(error_msg)
            raise Exception(error_msg)

    def generate_video(
        self,
        model: str,
        prompt: str,
        duration: int = 5,
        resolution: str = "720p",
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用API中转站生成视频

        Args:
            model: 模型标识
            prompt: 提示词
            duration: 视频时长（秒）
            resolution: 视频分辨率

        Returns:
            API返回的原始响应

        Raises:
            Exception: API调用失败时抛出异常
        """
        url = f"{self.base_url}/v1/videos/generations"

        payload = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution
        }

        # 合并额外参数
        payload.update(kwargs)

        app_logger.info(f"调用API中转站生视频: model={model}, duration={duration}, resolution={resolution}")

        try:
            session = requests.Session()
            session.trust_env = False

            response = session.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=300
            )

            if response.status_code >= 400:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                app_logger.error(error_msg)
                raise Exception(error_msg)

            result = response.json()

            app_logger.info(f"API中转站生视频成功: model={model}")
            return result

        except requests.RequestException as e:
            error_msg = f"API请求错误: {str(e)}"
            app_logger.error(error_msg)
            raise Exception(error_msg)


# 全局供应商实例
api_gateway_provider = ApiGatewayProvider()
