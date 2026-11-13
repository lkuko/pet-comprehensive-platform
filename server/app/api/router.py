"""总路由：统一注册用户端与管理端路由。

用户端挂载在 /user 下，管理端挂载在 /admin 下，
最终由 main.py 统一加上 /api/v1 前缀。
"""
from fastapi import APIRouter

from app.api.admin.v1 import auth as admin_auth
from app.api.user.v1 import auth as user_auth
from app.api.user.v1 import profile as user_profile
from app.common.response import ok

api_router = APIRouter()

# 用户端
user_router = APIRouter(prefix="/user")
user_router.include_router(user_auth.router)
user_router.include_router(user_profile.router)
api_router.include_router(user_router)

# 管理端
admin_router = APIRouter(prefix="/admin")
admin_router.include_router(admin_auth.router)
api_router.include_router(admin_router)


@api_router.get("/ping")
def ping():
    return ok({"pong": True})
