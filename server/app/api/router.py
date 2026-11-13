"""总路由：统一注册用户端与管理端路由。

Day 1 骨架仅提供 /ping 冒烟接口，用于验证统一响应与路由挂载。
后续业务路由按 user/v1、admin/v1 分模块注册。
"""
from fastapi import APIRouter

from app.common.response import ok

api_router = APIRouter()


@api_router.get("/ping")
def ping():
    return ok({"pong": True})
