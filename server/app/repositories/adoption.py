"""领养数据访问层。"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import AdoptionApplicationStatus
from app.models.pet import AdoptionApplication, AdoptionPet, PetCategory


class AdoptionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_pet(self, pet_id: int) -> AdoptionPet | None:
        return self.db.get(AdoptionPet, pet_id)

    def get_pet_for_update(self, pet_id: int) -> AdoptionPet | None:
        return self.db.get(AdoptionPet, pet_id, with_for_update=True)

    def get_category(self, category_id: int) -> PetCategory | None:
        return self.db.get(PetCategory, category_id)

    def list_active_categories(self) -> list[PetCategory]:
        stmt = select(PetCategory).where(PetCategory.status == "ACTIVE").order_by(PetCategory.sort)
        return list(self.db.scalars(stmt).all())

    def get_application(self, application_id: int) -> AdoptionApplication | None:
        return self.db.get(AdoptionApplication, application_id)

    def get_application_for_update(self, application_id: int) -> AdoptionApplication | None:
        return self.db.get(AdoptionApplication, application_id, with_for_update=True)

    def has_pending_application(self, user_id: int, pet_id: int) -> bool:
        stmt = (
            select(AdoptionApplication.id)
            .where(
                AdoptionApplication.user_id == user_id,
                AdoptionApplication.adoption_pet_id == pet_id,
                AdoptionApplication.status == AdoptionApplicationStatus.PENDING.value,
            )
            .limit(1)
        )
        return self.db.scalar(stmt) is not None
