"""公开端洗护/寄养接口：服务分类与套餐（游客可访问）。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.response import ApiResponse
from app.core.database import get_db
from app.schemas.care import CareCategoryOut, CarePackageOut
from app.services import care as care_service

router = APIRouter(prefix="/care", tags=["洗护寄养"])


@router.get("/categories", response_model=ApiResponse[list[CareCategoryOut]])
def list_categories(
    service_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=care_service.list_categories(db, service_type))


@router.get("/packages", response_model=ApiResponse[list[CarePackageOut]])
def list_packages(
    category_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=care_service.list_packages(db, category_id))
