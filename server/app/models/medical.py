"""医疗预约相关模型。

表：medical_locations（医疗点）、medical_doctors（医生）、
    medical_services（医疗项目）、doctor_schedules（医生排班）、
    medical_appointments（医疗预约单）。
"""
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PkType, TimestampMixin


class MedicalLocation(Base, TimestampMixin):
    """医疗点/诊所。"""

    __tablename__ = "medical_locations"

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)


class MedicalDoctor(Base, TimestampMixin):
    """医生（医疗人员信息由管理员维护，V1 无独立医生角色）。"""

    __tablename__ = "medical_doctors"

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    location_id: Mapped[int] = mapped_column(
        ForeignKey("medical_locations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    title: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    specialty: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)

    location: Mapped["MedicalLocation"] = relationship(lazy="selectin")


class MedicalService(Base, TimestampMixin):
    """医疗项目（体检、疫苗、驱虫、基础诊疗等）。"""

    __tablename__ = "medical_services"

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)


class DoctorSchedule(Base, TimestampMixin):
    """医生可预约时段及容量。

    schedule_date / start_time / end_time 均为业务时区（Asia/Shanghai）的日历语义。
    booked_count 不得超过 capacity；容量更新须在事务中锁定排班行。
    """

    __tablename__ = "doctor_schedules"
    __table_args__ = (
        UniqueConstraint(
            "doctor_id", "schedule_date", "start_time", "end_time",
            name="uq_schedule_slot",
        ),
        Index("ix_schedule_doctor_date", "doctor_id", "schedule_date"),
    )

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("medical_doctors.id"), nullable=False, index=True
    )
    location_id: Mapped[int] = mapped_column(
        ForeignKey("medical_locations.id"), nullable=False, index=True
    )
    schedule_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    booked_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)

    doctor: Mapped["MedicalDoctor"] = relationship(lazy="selectin")
    location: Mapped["MedicalLocation"] = relationship(lazy="selectin")


class MedicalAppointment(Base, TimestampMixin):
    """医疗预约单。"""

    __tablename__ = "medical_appointments"
    __table_args__ = (
        Index("ix_ma_user_status", "user_id", "status"),
        Index("ix_ma_schedule_status", "schedule_id", "status"),
    )

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    appointment_no: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    user_pet_id: Mapped[int] = mapped_column(
        ForeignKey("user_pets.id"), nullable=False, index=True
    )
    location_id: Mapped[int] = mapped_column(
        ForeignKey("medical_locations.id"), nullable=False, index=True
    )
    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("medical_doctors.id"), nullable=False, index=True
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("medical_services.id"), nullable=False, index=True
    )
    schedule_id: Mapped[int] = mapped_column(
        ForeignKey("doctor_schedules.id"), nullable=False, index=True
    )
    pet_name_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)
    service_name_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)
    appointment_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    symptom_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="PENDING_CONFIRMATION", index=True
    )
    review_comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(lazy="selectin")
    user_pet: Mapped["UserPet"] = relationship(lazy="selectin")
    location: Mapped["MedicalLocation"] = relationship(lazy="selectin")
    doctor: Mapped["MedicalDoctor"] = relationship(lazy="selectin")
    service: Mapped["MedicalService"] = relationship(lazy="selectin")
    schedule: Mapped["DoctorSchedule"] = relationship(lazy="selectin")
