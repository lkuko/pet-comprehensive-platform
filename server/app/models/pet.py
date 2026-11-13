"""宠物档案与领养相关模型。

表：user_pets（用户宠物）、pet_categories（领养分类）、
    adoption_pets（平台领养宠物）、adoption_pet_images（领养宠物图片）。
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PkType, TimestampMixin
from app.utils.time import utcnow


class UserPet(Base, TimestampMixin):
    """用户自己的宠物档案。"""

    __tablename__ = "user_pets"

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    breed: Mapped[str | None] = mapped_column(String(80), nullable=True)
    gender: Mapped[str] = mapped_column(String(20), nullable=False, default="UNKNOWN")
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True)
    weight: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    health_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_neutered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)


class PetCategory(Base, TimestampMixin):
    """领养宠物分类。"""

    __tablename__ = "pet_categories"

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")


class AdoptionPet(Base, TimestampMixin):
    """平台待领养宠物档案。"""

    __tablename__ = "adoption_pets"

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("pet_categories.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    breed: Mapped[str | None] = mapped_column(String(80), nullable=True)
    gender: Mapped[str] = mapped_column(String(20), nullable=False, default="UNKNOWN")
    age_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    health_status: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    vaccinated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    neutered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    personality: Mapped[str | None] = mapped_column(Text, nullable=True)
    adoption_requirements: Mapped[str] = mapped_column(Text, nullable=False, default="")
    region: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT", index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    category: Mapped["PetCategory"] = relationship(lazy="selectin")
    images: Mapped[list["AdoptionPetImage"]] = relationship(
        back_populates="pet",
        cascade="all, delete-orphan",
        order_by="AdoptionPetImage.sort",
        lazy="selectin",
    )


class AdoptionPetImage(Base):
    """领养宠物图片（多图，sort 升序，首图为封面）。"""

    __tablename__ = "adoption_pet_images"

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    adoption_pet_id: Mapped[int] = mapped_column(
        ForeignKey("adoption_pets.id"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    pet: Mapped["AdoptionPet"] = relationship(back_populates="images")
