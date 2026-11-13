"""用户端洗护/寄养预约接口：提交、列表、详情、取消。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import ApiResponse
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.care import CareAppointmentCreate, CareAppointmentOut
from app.services import care as care_service

router = APIRouter(prefix="/care/appointments", tags=["我的洗护寄养预约"])


@router.post("", response_model=ApiResponse[CareAppointmentOut])
def create_appointment(
    data: CareAppointmentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=care_service.create_appointment(db, user.id, data))


@router.get("", response_model=ApiResponse[list[CareAppointmentOut]])
def list_appointments(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=care_service.list_my_appointments(db, user.id))


@router.get("/{appointment_id}", response_model=ApiResponse[CareAppointmentOut])
def get_appointment(
    appointment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=care_service.get_my_appointment(db, user.id, appointment_id))


@router.post("/{appointment_id}/cancel", response_model=ApiResponse[CareAppointmentOut])
def cancel_appointment(
    appointment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=care_service.cancel_appointment(db, user.id, appointment_id))
