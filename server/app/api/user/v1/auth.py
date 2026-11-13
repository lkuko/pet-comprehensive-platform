"""用户端认证接口：注册、登录。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import ApiResponse
from app.core.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["用户认证"])


@router.post("/register", response_model=ApiResponse[TokenResponse])
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    return ApiResponse(data=auth_service.register(db, data))


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(data: LoginRequest, db: Session = Depends(get_db)):
    return ApiResponse(data=auth_service.login(db, data))
