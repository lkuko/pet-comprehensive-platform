"""洗护/寄养服务相关模型。

表：care_service_categories（服务分类）、care_service_packages（服务套餐）、
    care_appointments（洗护/寄养预约单）。

预约单通过价格快照（price_snapshot / total_price）固化下单时点的价格，
后续套餐调价不影响历史预约。
"""
from datetime import date, datetime
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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PkType, TimestampMixin


class CareServiceCategory(Base, TimestampMixin):
    """洗护/寄养服务分类（洗浴、美容、SPA、寄养等）。"""

    __tablename__ = "care_service_categories"

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    service_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)


class CareServicePackage(Base, TimestampMixin):
    """服务套餐（挂分类下，含价格）。"""

    __tablename__ = "care_service_packages"

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("care_service_categories.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)

    category: Mapped["CareServiceCategory"] = relationship(lazy="selectin")


class CareAppointment(Base, TimestampMixin):
    """洗护/寄养预约单。

    service_type 冗余存储分类类型，便于筛选；
    洗护存 appointment_time，寄养存 check_in_date / check_out_date，
    二者互斥（由业务层校验）。
    """

    __tablename__ = "care_appointments"
    __table_args__ = (
        Index("ix_ca_user_status", "user_id", "status"),
        Index("ix_ca_package_status", "package_id", "status"),
    )

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    appointment_no: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    user_pet_id: Mapped[int] = mapped_column(
        ForeignKey("user_pets.id"), nullable=False, index=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("care_service_categories.id"), nullable=False, index=True
    )
    package_id: Mapped[int] = mapped_column(
        ForeignKey("care_service_packages.id"), nullable=False, index=True
    )
    service_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    pet_name_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)
    category_name_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)
    package_name_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)
    price_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    appointment_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    check_in_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    check_out_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="PENDING_CONFIRMATION", index=True
    )
    review_comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(lazy="selectin")
    user_pet: Mapped["UserPet"] = relationship(lazy="selectin")
    category: Mapped["CareServiceCategory"] = relationship(lazy="selectin")
    package: Mapped["CareServicePackage"] = relationship(lazy="selectin")
