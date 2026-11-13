"""管理端认证接口：管理员登录。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import ApiResponse
from app.core.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["管理员认证"])


@router.post("/login", response_model=ApiResponse[TokenResponse])
def admin_login(data: LoginRequest, db: Session = Depends(get_db)):
    return ApiResponse(data=auth_service.admin_login(db, data))
