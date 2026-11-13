"""公开端领养接口（游客可访问）。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.pagination import PageResult
from app.common.response import ApiResponse
from app.core.database import get_db
from app.schemas.adoption import AdoptionPetDetail, PetCategoryOut
from app.services import adoption as adoption_service

router = APIRouter(tags=["公开领养"])


@router.get("/pet-categories", response_model=ApiResponse[list[PetCategoryOut]])
def list_categories(db: Session = Depends(get_db)):
    return ApiResponse(data=adoption_service.list_categories(db))


@router.get("/adoption-pets", response_model=ApiResponse[PageResult])
def list_pets(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category_id: int | None = Query(None),
    keyword: str | None = Query(None, max_length=50),
    db: Session = Depends(get_db),
):
    result = adoption_service.list_public_pets(db, page, page_size, category_id, keyword)
    return ApiResponse(data=result)


@router.get("/adoption-pets/{pet_id}", response_model=ApiResponse[AdoptionPetDetail])
def get_pet(pet_id: int, db: Session = Depends(get_db)):
    return ApiResponse(data=adoption_service.get_public_pet(db, pet_id))
