"""
Google GenAI Provider
使用 Gemini REST API 调用 Gemini 模型生成图片
"""
import base64
import json
import re
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

    def _apply_route_suffix(self, model: str, route_mode: Optional[str] = None) -> str:
        suffix_map = {
            "price": ":floor",
            "speed": ":nitro",
            "success_rate": ":stable",
        }

        suffix = suffix_map.get(route_mode or "")
        if not suffix:
            return model

        if model.endswith(":floor") or model.endswith(":nitro") or model.endswith(":stable"):
            return model

        return f"{model}{suffix}"

    def edit_image(
            self,
            model: str,
            prompt: str,
            image_urls: list[str],
            route_mode: Optional[str] = None,
            temperature: float = 0.7,
            max_tokens: int = 4096,
            **kwargs
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("API_GATEWAY_API_KEY is not configured")

        routed_model = self._apply_route_suffix(model, route_mode)
        url = f"{self.api_endpoint}/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": routed_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        *[
                            {"type": "image_url", "image_url": {"url": url}}
                            for url in image_urls[:5]
                        ],
                    ],
                }
            ],
            "stream": False,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        session = requests.Session()
        session.trust_env = False

        response = session.post(url, headers=headers, json=payload, timeout=180)

        if response.status_code >= 400:
            error_msg = f"Gemini image edit failed: {response.status_code} - {response.text}"
            app_logger.error(error_msg)
            raise RuntimeError(error_msg)

        result = response.json()
        images = self._extract_images_from_chat_result(result)

        if not images:
            raise RuntimeError("Gemini image edit did not return recognizable image data")

        return {"data": images}

    def _extract_images_from_chat_result(self, result: Dict[str, Any]) -> list[dict]:
        images = []

        def add_image_value(value: Any):
            if not isinstance(value, str) or not value:
                return

            value = value.strip()

            if value.startswith("http://") or value.startswith("https://"):
                images.append({"url": value})
                return

            data_url_match = re.search(
                r"data:image/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=\r\n]+",
                value,
            )
            if data_url_match:
                images.append({"b64_json": data_url_match.group(0)})
                return

            raw_base64_match = re.search(
                r"([A-Za-z0-9+/]{500,}={0,2})",
                value,
            )
            if raw_base64_match:
                images.append({"b64_json": raw_base64_match.group(1)})

        for choice in result.get("choices", []):
            message = choice.get("message", {})
            content = message.get("content")

            if isinstance(content, list):
                for part in content:
                    if not isinstance(part, dict):
                        continue

                    image_url = part.get("image_url")
                    if isinstance(image_url, dict):
                        add_image_value(image_url.get("url"))

                    for key in ("image", "b64_json", "data", "url", "text"):
                        add_image_value(part.get(key))

            elif isinstance(content, str):
                add_image_value(content)

        return images

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