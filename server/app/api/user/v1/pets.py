"""用户端宠物档案接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import ApiResponse
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.pet import UserPetCreate, UserPetOut, UserPetUpdate
from app.services import pet as pet_service

router = APIRouter(prefix="/pets", tags=["我的宠物"])


@router.get("", response_model=ApiResponse[list[UserPetOut]])
def list_pets(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ApiResponse(data=pet_service.list_pets(db, user.id))


@router.post("", response_model=ApiResponse[UserPetOut])
def create_pet(
    data: UserPetCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=pet_service.create_pet(db, user.id, data))


@router.get("/{pet_id}", response_model=ApiResponse[UserPetOut])
def get_pet(
    pet_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=pet_service.get_pet(db, user.id, pet_id))


@router.put("/{pet_id}", response_model=ApiResponse[UserPetOut])
def update_pet(
    pet_id: int,
    data: UserPetUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=pet_service.update_pet(db, user.id, pet_id, data))


@router.delete("/{pet_id}", response_model=ApiResponse)
def delete_pet(
    pet_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pet_service.delete_pet(db, user.id, pet_id)
    return ApiResponse()
