"""总路由：统一注册用户端、管理端与公开端路由。

用户端挂载在 /user 下，管理端挂载在 /admin 下，公开端挂载在 /public 下，
最终由 main.py 统一加上 /api/v1 前缀。
"""
from fastapi import APIRouter

from app.api import upload
from app.api.admin.v1 import adoption as admin_adoption
from app.api.admin.v1 import auth as admin_auth
from app.api.public.v1 import adoption as public_adoption
from app.api.user.v1 import auth as user_auth
from app.api.user.v1 import pets as user_pets
from app.api.user.v1 import profile as user_profile
from app.common.response import ok

api_router = APIRouter()

# 用户端
user_router = APIRouter(prefix="/user")
user_router.include_router(user_auth.router)
user_router.include_router(user_profile.router)
user_router.include_router(user_pets.router)
api_router.include_router(user_router)

# 管理端
admin_router = APIRouter(prefix="/admin")
admin_router.include_router(admin_auth.router)
admin_router.include_router(admin_adoption.router)
api_router.include_router(admin_router)

# 公开端（游客可访问）
public_router = APIRouter(prefix="/public")
public_router.include_router(public_adoption.router)
api_router.include_router(public_router)

# 通用上传（登录用户可用）
api_router.include_router(upload.router)


@api_router.get("/ping")
def ping():
    return ok({"pong": True})
