"""洗护/寄养服务数据访问层。"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.care import (
    CareAppointment,
    CareServiceCategory,
    CareServicePackage,
)


class CareRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_category(self, category_id: int) -> CareServiceCategory | None:
        return self.db.get(CareServiceCategory, category_id)

    def get_package(self, package_id: int) -> CareServicePackage | None:
        return self.db.get(CareServicePackage, package_id)

    def get_appointment(self, appointment_id: int) -> CareAppointment | None:
        return self.db.get(CareAppointment, appointment_id)

    def get_appointment_for_update(self, appointment_id: int) -> CareAppointment | None:
        return self.db.get(CareAppointment, appointment_id, with_for_update=True)

    def count_packages_for_category(self, category_id: int) -> int:
        stmt = select(CareServicePackage.id).where(
            CareServicePackage.category_id == category_id
        )
        return len(self.db.execute(stmt).all())

    def count_appointments_for_package(self, package_id: int) -> int:
        stmt = select(CareAppointment.id).where(
            CareAppointment.package_id == package_id
        )
        return len(self.db.execute(stmt).all())
