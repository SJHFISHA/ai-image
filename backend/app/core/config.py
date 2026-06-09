"""
配置模块 - 读取环境变量和配置信息
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""

    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:123456@localhost:3306/ai-image"

    # JWT 配置
    JWT_SECRET_KEY: str = "change-this-to-a-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7天

    # API 中转站配置
    API_GATEWAY_BASE_URL: str = "https://api.example.com/v1"
    API_GATEWAY_API_KEY: str = "sk-your-api-key"

    # 项目配置
    APP_NAME: str = "AI创作平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()
print(f"[DEBUG] DATABASE_URL = {settings.DATABASE_URL}")
