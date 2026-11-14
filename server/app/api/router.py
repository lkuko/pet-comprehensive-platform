"""总路由：统一注册用户端、管理端与公开端路由。

用户端挂载在 /user 下，管理端挂载在 /admin 下，公开端挂载在 /public 下，
最终由 main.py 统一加上 /api/v1 前缀。
"""
from fastapi import APIRouter

from app.api import upload
from app.api.admin.v1 import adoption as admin_adoption
from app.api.admin.v1 import adoption_applications as admin_adoption_applications
from app.api.admin.v1 import auth as admin_auth
from app.api.admin.v1 import care as admin_care
from app.api.admin.v1 import dashboard as admin_dashboard
from app.api.admin.v1 import mall as admin_mall
from app.api.admin.v1 import medical as admin_medical
from app.api.admin.v1 import notifications as admin_notifications
from app.api.public.v1 import adoption as public_adoption
from app.api.public.v1 import care as public_care
from app.api.public.v1 import mall as public_mall
from app.api.public.v1 import medical as public_medical
from app.api.user.v1 import addresses as user_addresses
from app.api.user.v1 import adoption_applications as user_adoption_applications
from app.api.user.v1 import auth as user_auth
from app.api.user.v1 import care_appointments as user_care_appointments
from app.api.user.v1 import cart as user_cart
from app.api.user.v1 import medical_appointments as user_medical_appointments
from app.api.user.v1 import orders as user_orders
from app.api.user.v1 import pets as user_pets
from app.api.user.v1 import profile as user_profile
from app.common.response import ok

api_router = APIRouter()

# 用户端
user_router = APIRouter(prefix="/user")
user_router.include_router(user_auth.router)
user_router.include_router(user_profile.router)
user_router.include_router(user_pets.router)
user_router.include_router(user_adoption_applications.router)
user_router.include_router(user_medical_appointments.router)
user_router.include_router(user_care_appointments.router)
user_router.include_router(user_cart.router)
user_router.include_router(user_orders.router)
user_router.include_router(user_addresses.router)
api_router.include_router(user_router)

# 管理端
admin_router = APIRouter(prefix="/admin")
admin_router.include_router(admin_auth.router)
admin_router.include_router(admin_adoption.router)
admin_router.include_router(admin_adoption_applications.router)
admin_router.include_router(admin_medical.router)
admin_router.include_router(admin_care.router)
admin_router.include_router(admin_mall.router)
admin_router.include_router(admin_dashboard.router)
admin_router.include_router(admin_notifications.router)
api_router.include_router(admin_router)

# 公开端（游客可访问）
public_router = APIRouter(prefix="/public")
public_router.include_router(public_adoption.router)
public_router.include_router(public_medical.router)
public_router.include_router(public_care.router)
public_router.include_router(public_mall.router)
api_router.include_router(public_router)

# 通用上传（登录用户可用）
api_router.include_router(upload.router)


@api_router.get("/ping")
def ping():
    return ok({"pong": True})
