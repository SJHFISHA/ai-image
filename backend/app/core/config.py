"""
配置模块 - 读取环境变量和配置信息
"""
from pathlib import Path
from pydantic_settings import BaseSettings

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """应用配置"""

    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:123456@localhost:3306/ai-image"

    # JWT 配置
    JWT_SECRET_KEY: str = "change-this-to-a-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7天

    # API 中转站配置
    API_GATEWAY_BASE_URL: str = ""
    API_GATEWAY_API_KEY: str = ""

    # 七牛云对象存储配置
    QINIU_ACCESS_KEY: str = ""
    QINIU_SECRET_KEY: str = ""
    QINIU_BUCKET: str = ""
    QINIU_DOMAIN: str = ""
    QINIU_REGION_ID: str = ""
    QINIU_PRIVATE_BUCKET: bool = False
    QINIU_PRIVATE_URL_EXPIRES: int = 3600

    # 项目配置
    APP_NAME: str = "AI创作平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()
