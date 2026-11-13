"""公开端医疗接口：医疗点、医生、医疗项目、可预约时段（游客可访问）。"""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.response import ApiResponse
from app.core.database import get_db
from app.schemas.medical import (
    DoctorScheduleOut,
    MedicalDoctorOut,
    MedicalLocationOut,
    MedicalServiceOut,
)
from app.services import medical as medical_service

router = APIRouter(prefix="/medical", tags=["医疗预约"])


@router.get("/locations", response_model=ApiResponse[list[MedicalLocationOut]])
def list_locations(db: Session = Depends(get_db)):
    return ApiResponse(data=medical_service.list_locations(db))


@router.get("/doctors", response_model=ApiResponse[list[MedicalDoctorOut]])
def list_doctors(
    location_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=medical_service.list_doctors(db, location_id))


@router.get("/services", response_model=ApiResponse[list[MedicalServiceOut]])
def list_services(db: Session = Depends(get_db)):
    return ApiResponse(data=medical_service.list_services(db))


@router.get("/schedules", response_model=ApiResponse[list[DoctorScheduleOut]])
def list_schedules(
    doctor_id: int | None = Query(None),
    location_id: int | None = Query(None),
    schedule_date: date | None = Query(None),
    db: Session = Depends(get_db),
):
    return ApiResponse(
        data=medical_service.list_schedules(db, doctor_id, location_id, schedule_date)
    )
