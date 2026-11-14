"""领养业务：分类、公开列表/详情、管理端宠物维护、领养申请与审核。"""
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from app.common.enums import (
    AdoptionApplicationStatus,
    AdoptionPetStatus,
    NotificationBusinessType,
)
from app.common.pagination import PageResult, normalize_page
from app.core.exceptions import ConflictError, NotFoundError, ParamError
from app.models.pet import AdoptionApplication, AdoptionPet, AdoptionPetImage, PetCategory
from app.models.user import User
from app.repositories.adoption import AdoptionRepository
from app.schemas.adoption import (
    AdoptionApplicationCreate,
    AdoptionApplicationOut,
    AdoptionPetCreate,
    AdoptionPetDetail,
    AdoptionPetListItem,
    AdoptionPetUpdate,
    PetCategoryOut,
)
from app.services import notification as notification_service
from app.utils.order_no import gen_no
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
    # 上架中与已领养的宠物均可查看详情（用户申请记录里可回看已领养宠物），
    # 草稿与已下架不对外展示。
    if pet.status not in (
        AdoptionPetStatus.AVAILABLE.value,
        AdoptionPetStatus.ADOPTED.value,
    ):
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


# ---------------- 领养申请 ----------------

def _to_application_out(app: AdoptionApplication) -> AdoptionApplicationOut:
    cover = app.pet.images[0].url if app.pet and app.pet.images else None
    return AdoptionApplicationOut(
        id=app.id,
        application_no=app.application_no,
        user_id=app.user_id,
        user_nickname=app.user.nickname if app.user else "",
        adoption_pet_id=app.adoption_pet_id,
        pet_name=app.pet.name if app.pet else "",
        pet_cover_url=cover,
        contact_name=app.contact_name,
        contact_phone=app.contact_phone,
        living_environment=app.living_environment,
        pet_experience=app.pet_experience,
        application_reason=app.application_reason,
        status=app.status,
        review_comment=app.review_comment,
        reviewer_id=app.reviewer_id,
        reviewed_at=to_iso(app.reviewed_at),
        created_at=to_iso(app.created_at),
    )


def _get_application(db: Session, application_id: int) -> AdoptionApplication:
    app = AdoptionRepository(db).get_application(application_id)
    if not app:
        raise NotFoundError("领养申请不存在")
    return app


def create_application(db: Session, user_id: int, data: AdoptionApplicationCreate) -> AdoptionApplicationOut:
    repo = AdoptionRepository(db)
    pet = repo.get_pet_for_update(data.adoption_pet_id)
    if not pet:
        raise NotFoundError("领养宠物不存在")
    if pet.status != AdoptionPetStatus.AVAILABLE.value:
        raise ConflictError("该宠物当前不可申请领养")
    if repo.has_pending_application(user_id, data.adoption_pet_id):
        raise ConflictError("你已提交过该宠物的领养申请，请勿重复提交")

    app = AdoptionApplication(
        application_no=gen_no("A"),
        user_id=user_id,
        adoption_pet_id=data.adoption_pet_id,
        contact_name=data.contact_name,
        contact_phone=data.contact_phone,
        living_environment=data.living_environment,
        pet_experience=data.pet_experience,
        application_reason=data.application_reason,
        status=AdoptionApplicationStatus.PENDING.value,
    )
    db.add(app)
    db.flush()
    notification_service.create_notification(
        db,
        NotificationBusinessType.ADOPTION_APPLICATION.value,
        app.id,
        "收到新的领养申请",
        f"用户申请领养「{pet.name}」",
    )
    db.commit()
    db.refresh(app)
    notification_service.push_new_business(
        NotificationBusinessType.ADOPTION_APPLICATION.value, app.id, "收到新的领养申请"
    )
    return _to_application_out(app)


def list_my_applications(db: Session, user_id: int) -> list[AdoptionApplicationOut]:
    stmt = (
        select(AdoptionApplication)
        .where(AdoptionApplication.user_id == user_id)
        .order_by(AdoptionApplication.id.desc())
    )
    rows = db.execute(stmt).scalars().all()
    return [_to_application_out(a) for a in rows]


def get_my_application(db: Session, user_id: int, application_id: int) -> AdoptionApplicationOut:
    app = _get_application(db, application_id)
    if app.user_id != user_id:
        raise NotFoundError("领养申请不存在")
    return _to_application_out(app)


def cancel_application(db: Session, user_id: int, application_id: int) -> AdoptionApplicationOut:
    app = AdoptionRepository(db).get_application_for_update(application_id)
    if not app or app.user_id != user_id:
        raise NotFoundError("领养申请不存在")
    if app.status != AdoptionApplicationStatus.PENDING.value:
        raise ConflictError("仅待审核的申请可撤回")
    app.status = AdoptionApplicationStatus.CANCELLED.value
    db.commit()
    return _to_application_out(app)


def list_admin_applications(
    db: Session,
    page: int,
    page_size: int,
    status: str | None = None,
    pet_id: int | None = None,
    keyword: str | None = None,
) -> PageResult:
    stmt = select(AdoptionApplication)
    if status:
        stmt = stmt.where(AdoptionApplication.status == status)
    if pet_id:
        stmt = stmt.where(AdoptionApplication.adoption_pet_id == pet_id)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                AdoptionApplication.application_no.like(like),
                AdoptionApplication.contact_name.like(like),
                AdoptionApplication.contact_phone.like(like),
            )
        )
    stmt = stmt.order_by(AdoptionApplication.id.desc())

    page, page_size = normalize_page(page, page_size)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.limit(page_size).offset((page - 1) * page_size)).scalars().all()
    return PageResult(
        items=[_to_application_out(a) for a in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


def approve_application(db: Session, admin: User, application_id: int) -> AdoptionApplicationOut:
    repo = AdoptionRepository(db)
    app = repo.get_application_for_update(application_id)
    if not app:
        raise NotFoundError("领养申请不存在")
    if app.status != AdoptionApplicationStatus.PENDING.value:
        raise ConflictError("该申请已被处理，无法重复审核")

    pet = repo.get_pet_for_update(app.adoption_pet_id)
    if not pet:
        raise NotFoundError("领养宠物不存在")
    if pet.status != AdoptionPetStatus.AVAILABLE.value:
        raise ConflictError("该宠物当前不可领养（可能已被领养或下架）")

    now = utcnow()
    app.status = AdoptionApplicationStatus.APPROVED.value
    app.reviewer_id = admin.id
    app.reviewed_at = now
    pet.status = AdoptionPetStatus.ADOPTED.value
    notification_service.mark_business_read(
        db, NotificationBusinessType.ADOPTION_APPLICATION.value, app.id
    )

    # 同一宠物其他待审核申请统一关闭
    db.execute(
        update(AdoptionApplication)
        .where(
            AdoptionApplication.adoption_pet_id == app.adoption_pet_id,
            AdoptionApplication.status == AdoptionApplicationStatus.PENDING.value,
            AdoptionApplication.id != app.id,
        )
        .values(
            status=AdoptionApplicationStatus.CLOSED.value,
            review_comment="该宠物已被领养，申请自动关闭",
            reviewer_id=admin.id,
            reviewed_at=now,
        )
    )
    db.commit()
    return _to_application_out(app)


def reject_application(
    db: Session, admin: User, application_id: int, comment: str
) -> AdoptionApplicationOut:
    app = AdoptionRepository(db).get_application_for_update(application_id)
    if not app:
        raise NotFoundError("领养申请不存在")
    if app.status != AdoptionApplicationStatus.PENDING.value:
        raise ConflictError("该申请已被处理，无法重复审核")

    app.status = AdoptionApplicationStatus.REJECTED.value
    app.review_comment = comment
    app.reviewer_id = admin.id
    app.reviewed_at = utcnow()
    notification_service.mark_business_read(
        db, NotificationBusinessType.ADOPTION_APPLICATION.value, app.id
    )
    db.commit()
    return _to_application_out(app)
