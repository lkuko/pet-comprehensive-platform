"""领养数据访问层。"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.pet import AdoptionPet, PetCategory


class AdoptionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_pet(self, pet_id: int) -> AdoptionPet | None:
        return self.db.get(AdoptionPet, pet_id)

    def get_category(self, category_id: int) -> PetCategory | None:
        return self.db.get(PetCategory, category_id)

    def list_active_categories(self) -> list[PetCategory]:
        stmt = select(PetCategory).where(PetCategory.status == "ACTIVE").order_by(PetCategory.sort)
        return list(self.db.scalars(stmt).all())
