"""管理端医疗接口：医疗点/医生/项目/排班 CRUD + 预约处理。"""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.pagination import PageResult
from app.common.response import ApiResponse
from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.user import User
from app.schemas.medical import (
    DoctorScheduleCreate,
    DoctorScheduleOut,
    DoctorScheduleUpdate,
    MedicalAppointmentOut,
    MedicalAppointmentReject,
    MedicalDoctorCreate,
    MedicalDoctorOut,
    MedicalDoctorUpdate,
    MedicalLocationCreate,
    MedicalLocationOut,
    MedicalLocationUpdate,
    MedicalServiceCreate,
    MedicalServiceOut,
    MedicalServiceUpdate,
)
from app.services import medical as medical_service

router = APIRouter(prefix="/medical", tags=["医疗资源管理"])


# ---------------- 医疗点 ----------------

@router.get("/locations", response_model=ApiResponse[list[MedicalLocationOut]])
def list_locations(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return ApiResponse(data=medical_service.list_admin_locations(db))


@router.post("/locations", response_model=ApiResponse[MedicalLocationOut])
def create_location(
    data: MedicalLocationCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=medical_service.create_location(db, data))


@router.put("/locations/{location_id}", response_model=ApiResponse[MedicalLocationOut])
def update_location(
    location_id: int,
    data: MedicalLocationUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=medical_service.update_location(db, location_id, data))


@router.delete("/locations/{location_id}", response_model=ApiResponse)
def delete_location(
    location_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    medical_service.delete_location(db, location_id)
    return ApiResponse()


# ---------------- 医生 ----------------

@router.get("/doctors", response_model=ApiResponse[list[MedicalDoctorOut]])
def list_doctors(
    location_id: int | None = Query(None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=medical_service.list_admin_doctors(db, location_id))


@router.post("/doctors", response_model=ApiResponse[MedicalDoctorOut])
def create_doctor(
    data: MedicalDoctorCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=medical_service.create_doctor(db, data))


@router.put("/doctors/{doctor_id}", response_model=ApiResponse[MedicalDoctorOut])
def update_doctor(
    doctor_id: int,
    data: MedicalDoctorUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=medical_service.update_doctor(db, doctor_id, data))


@router.delete("/doctors/{doctor_id}", response_model=ApiResponse)
def delete_doctor(
    doctor_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    medical_service.delete_doctor(db, doctor_id)
    return ApiResponse()


# ---------------- 医疗项目 ----------------

@router.get("/services", response_model=ApiResponse[list[MedicalServiceOut]])
def list_services(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return ApiResponse(data=medical_service.list_admin_services(db))


@router.post("/services", response_model=ApiResponse[MedicalServiceOut])
def create_service(
    data: MedicalServiceCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=medical_service.create_service(db, data))


@router.put("/services/{service_id}", response_model=ApiResponse[MedicalServiceOut])
def update_service(
    service_id: int,
    data: MedicalServiceUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=medical_service.update_service(db, service_id, data))


@router.delete("/services/{service_id}", response_model=ApiResponse)
def delete_service(
    service_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    medical_service.delete_service(db, service_id)
    return ApiResponse()


# ---------------- 排班 ----------------

@router.get("/schedules", response_model=ApiResponse[list[DoctorScheduleOut]])
def list_schedules(
    doctor_id: int | None = Query(None),
    schedule_date: date | None = Query(None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=medical_service.list_admin_schedules(db, doctor_id, schedule_date))


@router.post("/schedules", response_model=ApiResponse[DoctorScheduleOut])
def create_schedule(
    data: DoctorScheduleCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=medical_service.create_schedule(db, data))


@router.put("/schedules/{schedule_id}", response_model=ApiResponse[DoctorScheduleOut])
def update_schedule(
    schedule_id: int,
    data: DoctorScheduleUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=medical_service.update_schedule(db, schedule_id, data))


@router.delete("/schedules/{schedule_id}", response_model=ApiResponse)
def delete_schedule(
    schedule_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    medical_service.delete_schedule(db, schedule_id)
    return ApiResponse()


# ---------------- 预约处理 ----------------

@router.get("/appointments", response_model=ApiResponse[PageResult])
def list_appointments(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = Query(None),
    doctor_id: int | None = Query(None),
    location_id: int | None = Query(None),
    keyword: str | None = Query(None, max_length=50),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    result = medical_service.list_admin_appointments(
        db, page, page_size, status, doctor_id, location_id, keyword
    )
    return ApiResponse(data=result)


@router.post("/appointments/{appointment_id}/confirm", response_model=ApiResponse[MedicalAppointmentOut])
def confirm_appointment(
    appointment_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=medical_service.confirm_appointment(db, admin, appointment_id))


@router.post("/appointments/{appointment_id}/reject", response_model=ApiResponse[MedicalAppointmentOut])
def reject_appointment(
    appointment_id: int,
    data: MedicalAppointmentReject,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(
        data=medical_service.reject_appointment(db, admin, appointment_id, data.review_comment)
    )


@router.post("/appointments/{appointment_id}/complete", response_model=ApiResponse[MedicalAppointmentOut])
def complete_appointment(
    appointment_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=medical_service.complete_appointment(db, admin, appointment_id))
