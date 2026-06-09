"""
总路由汇总
"""
from fastapi import APIRouter

from app.api.routes import auth, points, model_prices, image, tasks, admin

# 创建总路由
api_router = APIRouter(prefix="/api")

# 注册各模块路由
api_router.include_router(auth.router)
api_router.include_router(points.router)
api_router.include_router(model_prices.router)
api_router.include_router(image.router)
api_router.include_router(tasks.router)
api_router.include_router(admin.router)

# TODO: 第八阶段添加充值路由
# from app.api.routes import recharge
# api_router.include_router(recharge.router)
