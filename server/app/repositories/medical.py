"""医疗预约数据访问层。"""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import MedicalAppointmentStatus
from app.models.medical import (
    DoctorSchedule,
    MedicalAppointment,
    MedicalDoctor,
    MedicalLocation,
    MedicalService,
)


class MedicalRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_location(self, location_id: int) -> MedicalLocation | None:
        return self.db.get(MedicalLocation, location_id)

    def get_doctor(self, doctor_id: int) -> MedicalDoctor | None:
        return self.db.get(MedicalDoctor, doctor_id)

    def get_service(self, service_id: int) -> MedicalService | None:
        return self.db.get(MedicalService, service_id)

    def get_schedule(self, schedule_id: int) -> DoctorSchedule | None:
        return self.db.get(DoctorSchedule, schedule_id)

    def get_schedule_for_update(self, schedule_id: int) -> DoctorSchedule | None:
        return self.db.get(DoctorSchedule, schedule_id, with_for_update=True)

    def get_appointment(self, appointment_id: int) -> MedicalAppointment | None:
        return self.db.get(MedicalAppointment, appointment_id)

    def get_appointment_for_update(self, appointment_id: int) -> MedicalAppointment | None:
        return self.db.get(MedicalAppointment, appointment_id, with_for_update=True)

    def list_doctor_schedules_on(self, doctor_id: int, day: date) -> list[DoctorSchedule]:
        stmt = (
            select(DoctorSchedule)
            .where(
                DoctorSchedule.doctor_id == doctor_id,
                DoctorSchedule.schedule_date == day,
            )
            .order_by(DoctorSchedule.start_time)
        )
        return list(self.db.scalars(stmt).all())

    def has_active_appointment(self, user_id: int, schedule_id: int) -> bool:
        """同一用户同一时段是否已有占位预约（待确认或已确认）。"""
        stmt = (
            select(MedicalAppointment.id)
            .where(
                MedicalAppointment.user_id == user_id,
                MedicalAppointment.schedule_id == schedule_id,
                MedicalAppointment.status.in_(
                    [
                        MedicalAppointmentStatus.PENDING_CONFIRMATION.value,
                        MedicalAppointmentStatus.CONFIRMED.value,
                    ]
                ),
            )
            .limit(1)
        )
        return self.db.scalar(stmt) is not None

    def count_unfinished_appointments_for_schedule(self, schedule_id: int) -> int:
        """排班下未完成（未取消/未拒绝/未完成）的预约数，用于删除保护。"""
        stmt = select(MedicalAppointment.id).where(
            MedicalAppointment.schedule_id == schedule_id,
            MedicalAppointment.status.in_(
                [
                    MedicalAppointmentStatus.PENDING_CONFIRMATION.value,
                    MedicalAppointmentStatus.CONFIRMED.value,
                ]
            ),
        )
        return len(self.db.execute(stmt).all())

    def count_schedules_for_doctor(self, doctor_id: int) -> int:
        stmt = select(DoctorSchedule.id).where(DoctorSchedule.doctor_id == doctor_id)
        return len(self.db.execute(stmt).all())

    def count_doctors_for_location(self, location_id: int) -> int:
        stmt = select(MedicalDoctor.id).where(MedicalDoctor.location_id == location_id)
        return len(self.db.execute(stmt).all())

    def count_appointments_for_service(self, service_id: int) -> int:
        stmt = select(MedicalAppointment.id).where(
            MedicalAppointment.service_id == service_id
        )
        return len(self.db.execute(stmt).all())
