"""用户端医疗预约接口：提交、列表、详情、取消。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import ApiResponse
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.medical import MedicalAppointmentCreate, MedicalAppointmentOut
from app.services import medical as medical_service

router = APIRouter(prefix="/medical/appointments", tags=["我的医疗预约"])


@router.post("", response_model=ApiResponse[MedicalAppointmentOut])
def create_appointment(
    data: MedicalAppointmentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=medical_service.create_appointment(db, user.id, data))


@router.get("", response_model=ApiResponse[list[MedicalAppointmentOut]])
def list_appointments(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=medical_service.list_my_appointments(db, user.id))


@router.get("/{appointment_id}", response_model=ApiResponse[MedicalAppointmentOut])
def get_appointment(
    appointment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=medical_service.get_my_appointment(db, user.id, appointment_id))


@router.post("/{appointment_id}/cancel", response_model=ApiResponse[MedicalAppointmentOut])
def cancel_appointment(
    appointment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=medical_service.cancel_appointment(db, user.id, appointment_id))
