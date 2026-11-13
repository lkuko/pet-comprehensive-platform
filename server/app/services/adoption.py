"""领养业务：分类、公开列表/详情、管理端宠物维护。"""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.common.enums import AdoptionPetStatus
from app.common.pagination import PageResult, normalize_page
from app.core.exceptions import NotFoundError, ParamError
from app.models.pet import AdoptionPet, AdoptionPetImage, PetCategory
from app.repositories.adoption import AdoptionRepository
from app.schemas.adoption import (
    AdoptionPetCreate,
    AdoptionPetDetail,
    AdoptionPetListItem,
    AdoptionPetUpdate,
    PetCategoryOut,
)
from app.utils.time import to_iso, utcnow


def list_categories(db: Session) -> list[PetCategoryOut]:
    rows = AdoptionRepository(db).list_active_categories()
    return [PetCategoryOut.model_validate(c) for c in rows]


def _get_pet(db: Session, pet_id: int) -> AdoptionPet:
    pet = AdoptionRepository(db).get_pet(pet_id)
    if not pet:
        raise NotFoundError("领养宠物不存在")
    return pet


def _to_list_item(pet: AdoptionPet) -> AdoptionPetListItem:
    cover = pet.images[0].url if pet.images else None
    return AdoptionPetListItem(
        id=pet.id,
        name=pet.name,
        breed=pet.breed,
        gender=pet.gender,
        age_months=pet.age_months,
        weight=float(pet.weight) if pet.weight is not None else None,
        region=pet.region,
        status=pet.status,
        category_id=pet.category_id,
        category_name=pet.category.name if pet.category else None,
        cover_url=cover,
        published_at=to_iso(pet.published_at),
    )


def _to_detail(pet: AdoptionPet) -> AdoptionPetDetail:
    item = _to_list_item(pet)
    return AdoptionPetDetail(
        **item.model_dump(),
        health_status=pet.health_status,
        vaccinated=pet.vaccinated,
        neutered=pet.neutered,
        personality=pet.personality,
        adoption_requirements=pet.adoption_requirements,
        description=pet.description,
        images=[img.url for img in pet.images],
        created_at=to_iso(pet.created_at),
        updated_at=to_iso(pet.updated_at),
    )


def list_public_pets(
    db: Session,
    page: int,
    page_size: int,
    category_id: int | None = None,
    keyword: str | None = None,
) -> PageResult:
    stmt = select(AdoptionPet).where(AdoptionPet.status == AdoptionPetStatus.AVAILABLE.value)
    if category_id:
        stmt = stmt.where(AdoptionPet.category_id == category_id)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(AdoptionPet.name.like(like), AdoptionPet.breed.like(like)))
    stmt = stmt.order_by(AdoptionPet.published_at.desc(), AdoptionPet.id.desc())

    page, page_size = normalize_page(page, page_size)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.limit(page_size).offset((page - 1) * page_size)).scalars().all()
    return PageResult(
        items=[_to_list_item(p) for p in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_public_pet(db: Session, pet_id: int) -> AdoptionPetDetail:
    pet = _get_pet(db, pet_id)
    if pet.status != AdoptionPetStatus.AVAILABLE.value:
        raise NotFoundError("领养宠物不存在或已下架")
    return _to_detail(pet)


def _require_category(db: Session, category_id: int) -> PetCategory:
    category = AdoptionRepository(db).get_category(category_id)
    if not category:
        raise NotFoundError("分类不存在")
    return category


def _set_images(db: Session, pet: AdoptionPet, urls: list[str]) -> None:
    pet.images.clear()
    for idx, url in enumerate(urls):
        pet.images.append(AdoptionPetImage(url=url, sort=idx))


def _apply_fields(pet: AdoptionPet, data: dict) -> None:
    for key, value in data.items():
        setattr(pet, key, value)


def create_pet(db: Session, data: AdoptionPetCreate) -> AdoptionPetDetail:
    _require_category(db, data.category_id)
    payload = data.model_dump(exclude={"images"})
    if payload["status"] == AdoptionPetStatus.AVAILABLE.value:
        payload["published_at"] = utcnow()
    pet = AdoptionPet(**payload)
    db.add(pet)
    db.flush()
    _set_images(db, pet, data.images)
    db.commit()
    return get_admin_pet(db, pet.id)


def update_pet(db: Session, pet_id: int, data: AdoptionPetUpdate) -> AdoptionPetDetail:
    pet = _get_pet(db, pet_id)
    payload = data.model_dump(exclude_unset=True)
    images = payload.pop("images", None)
    if "category_id" in payload:
        _require_category(db, payload["category_id"])
    _apply_fields(pet, payload)
    if images is not None:
        _set_images(db, pet, images)
    db.commit()
    return get_admin_pet(db, pet_id)


def update_status(db: Session, pet_id: int, status: str) -> AdoptionPetDetail:
    pet = _get_pet(db, pet_id)
    if status == AdoptionPetStatus.AVAILABLE.value and pet.status != status:
        if pet.published_at is None:
            pet.published_at = utcnow()
    pet.status = status
    db.commit()
    return get_admin_pet(db, pet_id)


def list_admin_pets(
    db: Session,
    page: int,
    page_size: int,
    status: str | None = None,
    keyword: str | None = None,
) -> PageResult:
    stmt = select(AdoptionPet)
    if status:
        stmt = stmt.where(AdoptionPet.status == status)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(AdoptionPet.name.like(like), AdoptionPet.breed.like(like)))
    stmt = stmt.order_by(AdoptionPet.id.desc())

    page, page_size = normalize_page(page, page_size)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.limit(page_size).offset((page - 1) * page_size)).scalars().all()
    return PageResult(
        items=[_to_list_item(p) for p in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_admin_pet(db: Session, pet_id: int) -> AdoptionPetDetail:
    return _to_detail(_get_pet(db, pet_id))
