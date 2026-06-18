"""
API中转站调用模块
"""
import mimetypes
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

    def _download_image_for_multipart(self, image_url: str, index: int) -> tuple[str, bytes, str]:
        """
        下载图片 URL，转换成 multipart 文件字段。
        """
        session = requests.Session()
        session.trust_env = False

        response = session.get(image_url, timeout=120)

        if response.status_code >= 400:
            raise Exception(f"参考图下载失败: {response.status_code} - {response.text}")

        if not response.content:
            raise Exception("参考图下载失败: 文件内容为空")

        content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if not content_type.startswith("image/"):
            content_type = "image/png"

        suffix = mimetypes.guess_extension(content_type) or ".png"
        filename = f"reference_{index}{suffix}"

        return filename, response.content, content_type

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

    def edit_image(
        self,
        model: str,
        prompt: str,
        image_urls: list[str],
        route_mode: Optional[str] = None,
        size: str = "1024x1024",
        count: int = 1,
        quality: str = "auto",
        background: str = "auto",
        moderation: str = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用 API 中转站 GPT Image 2 图片编辑接口。
        支持 1-2 张参考图，使用 multipart/form-data 多个同名 image 字段。
        """
        if not image_urls:
            raise Exception("图片编辑至少需要 1 张参考图")

        url = f"{self.base_url}/v1/images/edits"
        routed_model = self._apply_route_suffix(model, route_mode)

        data = {
            "model": routed_model,
            "prompt": prompt,
            "n": str(count),
            "size": size,
            "quality": quality,
            "background": background,
            "moderation": moderation,
        }

        files = []
        for index, image_url in enumerate(image_urls[:2], start=1):
            filename, content, content_type = self._download_image_for_multipart(image_url, index)
            files.append(
                ("image", (filename, content, content_type))
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        app_logger.info(
            f"调用API中转站图片编辑: model={routed_model}, size={size}, "
            f"count={count}, refs={len(files)}, route_mode={route_mode}"
        )

        try:
            session = requests.Session()
            session.trust_env = False

            response = session.post(
                url,
                data=data,
                files=files,
                headers=headers,
                timeout=300,
            )

            if response.status_code >= 400:
                error_msg = f"API图片编辑调用失败: {response.status_code} - {response.text}"
                app_logger.error(error_msg)
                raise Exception(error_msg)

            result = response.json()
            app_logger.info(f"API中转站图片编辑成功: model={routed_model}")
            return result

        except requests.RequestException as e:
            error_msg = f"API图片编辑请求错误: {str(e)}"
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
