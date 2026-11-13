"""洗护/寄养相关 Schema：服务分类、服务套餐、预约。"""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.common.enums import CareAppointmentStatus, EnableStatus, ServiceType


# ---------------- 服务分类 ----------------

class CareCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    service_type: ServiceType
    description: str | None = None
    sort: int = Field(default=0, ge=0)
    status: EnableStatus = EnableStatus.ACTIVE


class CareCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    service_type: ServiceType | None = None
    description: str | None = None
    sort: int | None = Field(default=None, ge=0)
    status: EnableStatus | None = None


class CareCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    service_type: str
    description: str | None
    sort: int
    status: str


# ---------------- 服务套餐 ----------------

class CarePackageCreate(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=50)
    description: str | None = None
    price: Decimal = Field(default=0, ge=0, max_digits=10, decimal_places=2)
    duration_minutes: int = Field(default=60, ge=1)
    status: EnableStatus = EnableStatus.ACTIVE


class CarePackageUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    duration_minutes: int | None = Field(default=None, ge=1)
    status: EnableStatus | None = None


class CarePackageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    name: str
    description: str | None
    price: Decimal
    duration_minutes: int
    status: str


# ---------------- 预约 ----------------

class CareAppointmentCreate(BaseModel):
    user_pet_id: int
    package_id: int
    appointment_time: datetime | None = None
    check_in_date: date | None = None
    check_out_date: date | None = None
    contact_phone: str = Field(min_length=1, max_length=20)
    note: str | None = None

    @model_validator(mode="after")
    def _check_fields(self) -> "CareAppointmentCreate":
        has_appt = self.appointment_time is not None
        has_in = self.check_in_date is not None
        has_out = self.check_out_date is not None
        # 洗护与寄养字段互斥：要么填预约时间，要么填入住/离店日期，不可混填
        if has_appt and (has_in or has_out):
            raise ValueError("洗护预约时间与寄养入住/离店日期不可同时填写")
        if not has_appt and not (has_in and has_out):
            raise ValueError("请填写洗护预约时间，或同时填写寄养入住与离店日期")
        return self


class CareAppointmentReject(BaseModel):
    review_comment: str = Field(min_length=1, max_length=500)


class CareAppointmentOut(BaseModel):
    id: int
    appointment_no: str
    user_id: int
    user_nickname: str
    user_pet_id: int
    pet_name: str
    category_id: int
    category_name: str
    package_id: int
    package_name: str
    service_type: str
    price_snapshot: Decimal
    total_price: Decimal
    appointment_time: str | None
    check_in_date: date | None
    check_out_date: date | None
    contact_phone: str
    note: str | None
    status: str
    review_comment: str | None
    reviewed_at: str | None
    created_at: str
