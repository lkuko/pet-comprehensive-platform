"""管理端洗护/寄养接口：分类/套餐 CRUD + 预约处理。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.pagination import PageResult
from app.common.response import ApiResponse
from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.user import User
from app.schemas.care import (
    CareAppointmentOut,
    CareAppointmentReject,
    CareCategoryCreate,
    CareCategoryOut,
    CareCategoryUpdate,
    CarePackageCreate,
    CarePackageOut,
    CarePackageUpdate,
)
from app.services import care as care_service

router = APIRouter(prefix="/care", tags=["洗护寄养资源管理"])


# ---------------- 分类 ----------------

@router.get("/categories", response_model=ApiResponse[list[CareCategoryOut]])
def list_categories(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return ApiResponse(data=care_service.list_admin_categories(db))


@router.post("/categories", response_model=ApiResponse[CareCategoryOut])
def create_category(
    data: CareCategoryCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=care_service.create_category(db, data))


@router.put("/categories/{category_id}", response_model=ApiResponse[CareCategoryOut])
def update_category(
    category_id: int,
    data: CareCategoryUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=care_service.update_category(db, category_id, data))


@router.delete("/categories/{category_id}", response_model=ApiResponse)
def delete_category(
    category_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    care_service.delete_category(db, category_id)
    return ApiResponse()


# ---------------- 套餐 ----------------

@router.get("/packages", response_model=ApiResponse[list[CarePackageOut]])
def list_packages(
    category_id: int | None = Query(None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=care_service.list_admin_packages(db, category_id))


@router.post("/packages", response_model=ApiResponse[CarePackageOut])
def create_package(
    data: CarePackageCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=care_service.create_package(db, data))


@router.put("/packages/{package_id}", response_model=ApiResponse[CarePackageOut])
def update_package(
    package_id: int,
    data: CarePackageUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=care_service.update_package(db, package_id, data))


@router.delete("/packages/{package_id}", response_model=ApiResponse)
def delete_package(
    package_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    care_service.delete_package(db, package_id)
    return ApiResponse()


# ---------------- 预约处理 ----------------

@router.get("/appointments", response_model=ApiResponse[PageResult])
def list_appointments(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = Query(None),
    service_type: str | None = Query(None),
    keyword: str | None = Query(None, max_length=50),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    result = care_service.list_admin_appointments(
        db, page, page_size, status, service_type, keyword
    )
    return ApiResponse(data=result)


@router.post("/appointments/{appointment_id}/confirm", response_model=ApiResponse[CareAppointmentOut])
def confirm_appointment(
    appointment_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=care_service.confirm_appointment(db, admin, appointment_id))


@router.post("/appointments/{appointment_id}/reject", response_model=ApiResponse[CareAppointmentOut])
def reject_appointment(
    appointment_id: int,
    data: CareAppointmentReject,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(
        data=care_service.reject_appointment(db, admin, appointment_id, data.review_comment)
    )


@router.post("/appointments/{appointment_id}/complete", response_model=ApiResponse[CareAppointmentOut])
def complete_appointment(
    appointment_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=care_service.complete_appointment(db, admin, appointment_id))
