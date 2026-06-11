"""
Provider工厂模块
根据provider_key返回对应的provider实例
"""
from app.providers.api_gateway_provider import api_gateway_provider
from app.providers.base import BaseProvider
from app.utils.logger import app_logger


def get_image_provider(provider_key: str) -> BaseProvider:
    """
    根据provider_key获取图片生成provider

    Args:
        provider_key: 供应商标识

    Returns:
        对应的provider实例

    Raises:
        ValueError: 不支持的provider_key时抛出异常
    """
    if provider_key == "api_gateway":
        return api_gateway_provider

    # Google GenAI provider (延迟导入，避免依赖问题)
    if provider_key == "google_genai":
        from app.providers.google_genai_provider import google_genai_provider
        return google_genai_provider

    raise ValueError(f"不支持的图片供应商: {provider_key}")
