"""管理端领养宠物维护接口。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.pagination import PageResult
from app.common.response import ApiResponse
from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.user import User
from app.schemas.adoption import (
    AdoptionPetCreate,
    AdoptionPetDetail,
    AdoptionPetStatusUpdate,
    AdoptionPetUpdate,
)
from app.services import adoption as adoption_service

router = APIRouter(prefix="/adoption-pets", tags=["领养宠物管理"])


@router.get("", response_model=ApiResponse[PageResult])
def list_pets(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = Query(None),
    keyword: str | None = Query(None, max_length=50),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    result = adoption_service.list_admin_pets(db, page, page_size, status, keyword)
    return ApiResponse(data=result)


@router.post("", response_model=ApiResponse[AdoptionPetDetail])
def create_pet(
    data: AdoptionPetCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=adoption_service.create_pet(db, data))


@router.get("/{pet_id}", response_model=ApiResponse[AdoptionPetDetail])
def get_pet(
    pet_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=adoption_service.get_admin_pet(db, pet_id))


@router.put("/{pet_id}", response_model=ApiResponse[AdoptionPetDetail])
def update_pet(
    pet_id: int,
    data: AdoptionPetUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=adoption_service.update_pet(db, pet_id, data))


@router.patch("/{pet_id}/status", response_model=ApiResponse[AdoptionPetDetail])
def update_status(
    pet_id: int,
    data: AdoptionPetStatusUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=adoption_service.update_status(db, pet_id, data.status.value))
