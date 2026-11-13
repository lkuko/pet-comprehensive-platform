"""用户宠物档案业务：列表、新增、详情、修改、软删除。"""
from sqlalchemy.orm import Session

from app.common.enums import UserPetStatus
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.pet import UserPet
from app.repositories.pet import UserPetRepository
from app.schemas.pet import UserPetCreate, UserPetOut, UserPetUpdate


def _get_owned(db: Session, user_id: int, pet_id: int) -> UserPet:
    pet = UserPetRepository(db).get_by_id(pet_id)
    if not pet:
        raise NotFoundError("宠物档案不存在")
    if pet.user_id != user_id:
        raise ForbiddenError("无权访问该宠物档案")
    return pet


def list_pets(db: Session, user_id: int) -> list[UserPetOut]:
    pets = UserPetRepository(db).list_by_user(user_id)
    return [UserPetOut.model_validate(p) for p in pets]


def create_pet(db: Session, user_id: int, data: UserPetCreate) -> UserPetOut:
    pet = UserPet(user_id=user_id, **data.model_dump())
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return UserPetOut.model_validate(pet)


def get_pet(db: Session, user_id: int, pet_id: int) -> UserPetOut:
    return UserPetOut.model_validate(_get_owned(db, user_id, pet_id))


def update_pet(db: Session, user_id: int, pet_id: int, data: UserPetUpdate) -> UserPetOut:
    pet = _get_owned(db, user_id, pet_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(pet, key, value)
    db.commit()
    db.refresh(pet)
    return UserPetOut.model_validate(pet)


def delete_pet(db: Session, user_id: int, pet_id: int) -> None:
    """软删除：停用档案，不物理删除（保留历史关联）。"""
    pet = _get_owned(db, user_id, pet_id)
    pet.status = UserPetStatus.INACTIVE.value
    db.commit()
