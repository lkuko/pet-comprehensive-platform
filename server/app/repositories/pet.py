"""用户宠物档案数据访问层。"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.pet import UserPet


class UserPetRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, pet_id: int) -> UserPet | None:
        return self.db.get(UserPet, pet_id)

    def list_by_user(self, user_id: int, only_active: bool = True) -> list[UserPet]:
        stmt = select(UserPet).where(UserPet.user_id == user_id)
        if only_active:
            stmt = stmt.where(UserPet.status == "ACTIVE")
        return list(self.db.scalars(stmt.order_by(UserPet.created_at.desc())).all())
