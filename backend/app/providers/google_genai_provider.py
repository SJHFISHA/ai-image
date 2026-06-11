"""
Google GenAI Provider
使用 google-generativeai SDK 调用 Gemini 模型生成图片
"""
import base64
from typing import Dict, Any

from app.core.config import settings
from app.providers.base import BaseProvider
from app.utils.logger import app_logger


class GoogleGenAIProvider(BaseProvider):
    """Google GenAI 图片生成Provider"""

    def __init__(self):
        self.api_key = settings.GOOGLE_GENAI_API_KEY
        self.api_endpoint = settings.GOOGLE_GENAI_API_ENDPOINT

    def _configure(self):
        """配置 Google GenAI SDK"""
        if not self.api_key:
            raise ValueError("GOOGLE_GENAI_API_KEY is not configured")

        try:
            import google.generativeai as genai

            genai.configure(
                api_key=self.api_key,
                client_options={"api_endpoint": self.api_endpoint} if self.api_endpoint else None,
            )
        except ImportError:
            raise ValueError("请安装 google-generativeai: pip install google-generativeai")

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
            size: 图片尺寸（当前Google GenAI不支持尺寸参数）
            count: 生成数量
            **kwargs: 其他参数

        Returns:
            统一格式: {"data": [{"b64_json": "base64字符串"}]}
        """
        self._configure()

        import google.generativeai as genai

        genai_model = genai.GenerativeModel(model)
        images = []

        for _ in range(count):
            try:
                response = genai_model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        response_modalities=["IMAGE", "TEXT"],
                    ),
                )

                candidates = getattr(response, "candidates", None) or []
                if not candidates:
                    continue

                content = getattr(candidates[0], "content", None)
                parts = getattr(content, "parts", None) or []

                for part in parts:
                    inline_data = getattr(part, "inline_data", None)
                    if inline_data and getattr(inline_data, "data", None):
                        image_base64 = base64.b64encode(inline_data.data).decode("utf-8")
                        images.append({"b64_json": image_base64})
            except Exception as e:
                app_logger.error(f"Google GenAI 生成图片失败: {str(e)}")
                raise

        if not images:
            raise RuntimeError("Google GenAI 未返回图片数据")

        app_logger.info(f"Google GenAI 生图成功: model={model}, count={len(images)}")

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
