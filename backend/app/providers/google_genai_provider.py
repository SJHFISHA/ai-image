"""
Google GenAI Provider
使用 Gemini REST API 调用 Gemini 模型生成图片
"""
import base64
import json
from typing import Dict, Any, Optional

import requests

from app.core.config import settings
from app.providers.base import BaseProvider
from app.utils.logger import app_logger


class GoogleGenAIProvider(BaseProvider):
    """Google GenAI 图片生成Provider（REST API版本）"""

    def __init__(self):
        # 所有模型共用 API_GATEWAY_API_KEY
        self.api_key = settings.API_GATEWAY_API_KEY
        self.api_endpoint = settings.API_GATEWAY_BASE_URL

    def _map_to_gemini_config(
        self,
        aspect_ratio: Optional[str] = None,
        image_size: Optional[str] = None
    ) -> Dict[str, str]:
        """
        将数据库配置映射到 Gemini API 参数

        Args:
            aspect_ratio: 宽高比，如 "1:1", "16:9"
            image_size: 分辨率，如 "1K", "2K", "4K"

        Returns:
            Gemini API 的 imageConfig 参数
        """
        # 宽高比映射（验证有效性）
        valid_aspect_ratios = ["1:1", "16:9", "9:16", "4:3", "3:4"]
        aspect = aspect_ratio if aspect_ratio in valid_aspect_ratios else "1:1"

        # 分辨率映射（验证有效性）
        valid_image_sizes = ["1K", "2K", "4K"]
        size = image_size if image_size in valid_image_sizes else "1K"

        return {
            "aspectRatio": aspect,
            "imageSize": size
        }

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
            size: 图片尺寸（被 aspect_ratio 和 image_size 覆盖）
            count: 生成数量
            **kwargs: 其他参数，包含 aspect_ratio 和 image_size

        Returns:
            统一格式: {"data": [{"b64_json": "base64字符串"}]}
        """
        if not self.api_key:
            raise ValueError("API_GATEWAY_API_KEY is not configured")

        # 从 kwargs 中获取 aspect_ratio 和 image_size
        aspect_ratio = kwargs.get("aspect_ratio")
        image_size = kwargs.get("image_size")

        # 映射到 Gemini API 参数
        gemini_config = self._map_to_gemini_config(aspect_ratio, image_size)

        images = []

        for _ in range(count):
            try:
                # 构建请求 URL
                url = f"{self.api_endpoint}/v1beta/models/{model}:generateContent"

                # 构建请求头
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }

                # 构建请求体
                payload = {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [
                                {"text": prompt}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "response_modalities": ["IMAGE", "TEXT"],
                        "imageConfig": gemini_config
                    }
                }

                app_logger.info(
                    f"调用 Gemini REST API: model={model}, "
                    f"aspect_ratio={gemini_config['aspectRatio']}, "
                    f"image_size={gemini_config['imageSize']}"
                )

                # 发送请求（禁用代理）
                session = requests.Session()
                session.trust_env = False

                response = session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=60
                )

                if response.status_code != 200:
                    error_msg = f"Gemini API 请求失败: {response.status_code} - {response.text}"
                    app_logger.error(error_msg)
                    raise RuntimeError(error_msg)

                result = response.json()

                # 解析响应，提取图片数据
                candidates = result.get("candidates", [])
                if not candidates:
                    continue

                content = candidates[0].get("content", {})
                parts = content.get("parts", [])

                for part in parts:
                    inline_data = part.get("inlineData", {})
                    if inline_data and inline_data.get("data"):
                        image_base64 = inline_data["data"]
                        images.append({"b64_json": image_base64})

            except Exception as e:
                app_logger.error(f"Gemini REST API 生成图片失败: {str(e)}")
                raise

        if not images:
            raise RuntimeError("Gemini REST API 未返回图片数据")

        app_logger.info(f"Gemini REST API 生图成功: model={model}, count={len(images)}")

        return {"data": images}

    def generate_video(
        self,
        model: str,
        prompt: str,
        duration: int = 5,
        resolution: str = "720p",
        **kwargs
    ) -> Dict[str, Any]:
        """生成视频（暂不支持）"""
        raise NotImplementedError("Google GenAI provider 暂不支持视频生成")


google_genai_provider = GoogleGenAIProvider()