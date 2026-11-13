"""管理端领养申请审核接口：审核列表、通过、拒绝。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.pagination import PageResult
from app.common.response import ApiResponse
from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.user import User
from app.schemas.adoption import AdoptionApplicationOut, AdoptionApplicationReject
from app.services import adoption as adoption_service

router = APIRouter(prefix="/adoption-applications", tags=["领养申请审核"])


@router.get("", response_model=ApiResponse[PageResult])
def list_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = Query(None),
    pet_id: int | None = Query(None),
    keyword: str | None = Query(None, max_length=50),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    result = adoption_service.list_admin_applications(
        db, page, page_size, status, pet_id, keyword
    )
    return ApiResponse(data=result)


@router.post("/{application_id}/approve", response_model=ApiResponse[AdoptionApplicationOut])
def approve_application(
    application_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=adoption_service.approve_application(db, admin, application_id))


@router.post("/{application_id}/reject", response_model=ApiResponse[AdoptionApplicationOut])
def reject_application(
    application_id: int,
    data: AdoptionApplicationReject,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(
        data=adoption_service.reject_application(db, admin, application_id, data.review_comment)
    )
