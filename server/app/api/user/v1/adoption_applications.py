"""用户端领养申请接口：提交、列表、详情、撤回。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import ApiResponse
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.adoption import AdoptionApplicationCreate, AdoptionApplicationOut
from app.services import adoption as adoption_service

router = APIRouter(prefix="/adoption-applications", tags=["我的领养申请"])


@router.post("", response_model=ApiResponse[AdoptionApplicationOut])
def create_application(
    data: AdoptionApplicationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=adoption_service.create_application(db, user.id, data))


@router.get("", response_model=ApiResponse[list[AdoptionApplicationOut]])
def list_applications(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=adoption_service.list_my_applications(db, user.id))


@router.get("/{application_id}", response_model=ApiResponse[AdoptionApplicationOut])
def get_application(
    application_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=adoption_service.get_my_application(db, user.id, application_id))


@router.post("/{application_id}/cancel", response_model=ApiResponse[AdoptionApplicationOut])
def cancel_application(
    application_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=adoption_service.cancel_application(db, user.id, application_id))
