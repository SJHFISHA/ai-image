"""
FastAPI 应用入口
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.router import api_router
from app.utils.logger import app_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    app_logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    yield
    # 关闭时执行
    app_logger.info(f"👋 {settings.APP_NAME} 已关闭")


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用

    Returns:
        FastAPI 实例
    """
    # 创建应用
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI创作平台后端API",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应该限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(api_router)

    # 全局异常处理
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """HTTPException 处理"""
        # 根据状态码映射业务错误码
        status_code_mapping = {
            400: 40000,
            401: 40100,
            403: 40300,
            404: 40400,
            409: 40900,
            500: 50000,
        }
        business_code = status_code_mapping.get(exc.status_code, 50000)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": business_code,
                "message": exc.detail,
                "data": None,
                "success": False
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """参数校验错误处理"""
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            errors.append(f"{field}: {error['msg']}")

        error_message = "参数校验失败: " + "; ".join(errors)
        app_logger.warning(f"参数校验错误: {error_message}")

        return JSONResponse(
            status_code=422,
            content={
                "code": 40001,
                "message": error_message,
                "data": None,
                "success": False
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """未捕获异常处理"""
        app_logger.error(f"未捕获的异常: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "code": 50000,
                "message": "服务器内部错误，请稍后重试",
                "data": None,
                "success": False
            }
        )

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
