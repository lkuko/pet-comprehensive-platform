"""医疗预约相关 Schema：医疗点、医生、项目、排班、预约。"""
from datetime import date, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import EnableStatus, MedicalAppointmentStatus


# ---------------- 医疗点 ----------------

class MedicalLocationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    address: str = Field(default="", max_length=255)
    phone: str = Field(default="", max_length=20)
    description: str | None = None
    status: EnableStatus = EnableStatus.ACTIVE


class MedicalLocationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    address: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    description: str | None = None
    status: EnableStatus | None = None


class MedicalLocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    phone: str
    description: str | None
    status: str


# ---------------- 医生 ----------------

class MedicalDoctorCreate(BaseModel):
    location_id: int
    name: str = Field(min_length=1, max_length=50)
    avatar_url: str | None = Field(default=None, max_length=500)
    title: str = Field(default="", max_length=50)
    specialty: str = Field(default="", max_length=255)
    status: EnableStatus = EnableStatus.ACTIVE


class MedicalDoctorUpdate(BaseModel):
    location_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=50)
    avatar_url: str | None = Field(default=None, max_length=500)
    title: str | None = Field(default=None, max_length=50)
    specialty: str | None = Field(default=None, max_length=255)
    status: EnableStatus | None = None


class MedicalDoctorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    location_id: int
    name: str
    avatar_url: str | None
    title: str
    specialty: str
    status: str


# ---------------- 医疗项目 ----------------

class MedicalServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str | None = None
    reference_price: Decimal = Field(default=0, ge=0, max_digits=10, decimal_places=2)
    duration_minutes: int = Field(default=30, ge=1)
    status: EnableStatus = EnableStatus.ACTIVE


class MedicalServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = None
    reference_price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    duration_minutes: int | None = Field(default=None, ge=1)
    status: EnableStatus | None = None


class MedicalServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    reference_price: Decimal
    duration_minutes: int
    status: str


# ---------------- 排班 ----------------

class DoctorScheduleCreate(BaseModel):
    doctor_id: int
    location_id: int
    schedule_date: date
    start_time: time
    end_time: time
    capacity: int = Field(ge=1)
    status: EnableStatus = EnableStatus.ACTIVE


class DoctorScheduleUpdate(BaseModel):
    location_id: int | None = None
    schedule_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    capacity: int | None = Field(default=None, ge=1)
    status: EnableStatus | None = None


class DoctorScheduleOut(BaseModel):
    id: int
    doctor_id: int
    location_id: int
    schedule_date: date
    start_time: time
    end_time: time
    capacity: int
    booked_count: int
    status: str
    remaining: int


# ---------------- 预约 ----------------

class MedicalAppointmentCreate(BaseModel):
    user_pet_id: int
    schedule_id: int
    service_id: int
    symptom_note: str | None = None
    contact_phone: str = Field(min_length=1, max_length=20)


class MedicalAppointmentReject(BaseModel):
    review_comment: str = Field(min_length=1, max_length=500)


class MedicalAppointmentOut(BaseModel):
    id: int
    appointment_no: str
    user_id: int
    user_nickname: str
    user_pet_id: int
    pet_name: str
    location_id: int
    location_name: str
    doctor_id: int
    doctor_name: str
    service_id: int
    service_name: str
    schedule_id: int
    schedule_date: date | None
    start_time: time | None
    end_time: time | None
    appointment_time: str
    symptom_note: str | None
    contact_phone: str
    status: str
    review_comment: str | None
    reviewed_at: str | None
    created_at: str
