"""用户端个人资料接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import ApiResponse
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.user import ProfileUpdate, UserOut
from app.services import user as user_service

router = APIRouter(prefix="/profile", tags=["用户资料"])


@router.get("", response_model=ApiResponse[UserOut])
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ApiResponse(data=user_service.get_profile(db, user.id))


@router.put("", response_model=ApiResponse[UserOut])
def update_profile(
    data: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=user_service.update_profile(db, user.id, data))
