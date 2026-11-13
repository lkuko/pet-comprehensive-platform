"""洗护/寄养业务：公开查询、预约（价格快照 + 类型互斥校验）、取消、管理端维护与处理。"""
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.common.enums import (
    CareAppointmentStatus,
    EnableStatus,
    ServiceType,
    UserPetStatus,
)
from app.common.pagination import PageResult, normalize_page
from app.core.exceptions import ConflictError, NotFoundError, ParamError
from app.models.care import CareAppointment, CareServiceCategory, CareServicePackage
from app.models.pet import UserPet
from app.models.user import User
from app.repositories.care import CareRepository
from app.schemas.care import (
    CareAppointmentCreate,
    CareAppointmentOut,
    CareCategoryCreate,
    CareCategoryOut,
    CareCategoryUpdate,
    CarePackageCreate,
    CarePackageOut,
    CarePackageUpdate,
)
from app.utils.order_no import gen_no
from app.utils.time import business_tz, to_iso, to_utc_naive, utcnow


# ---------------- 公开查询 ----------------

def list_categories(
    db: Session, service_type: str | None = None
) -> list[CareCategoryOut]:
    stmt = select(CareServiceCategory).where(
        CareServiceCategory.status == EnableStatus.ACTIVE.value
    )
    if service_type:
        stmt = stmt.where(CareServiceCategory.service_type == service_type)
    stmt = stmt.order_by(CareServiceCategory.sort, CareServiceCategory.id)
    rows = db.execute(stmt).scalars().all()
    return [CareCategoryOut.model_validate(r) for r in rows]


def list_packages(
    db: Session, category_id: int | None = None
) -> list[CarePackageOut]:
    stmt = select(CareServicePackage).where(
        CareServicePackage.status == EnableStatus.ACTIVE.value
    )
    if category_id:
        stmt = stmt.where(CareServicePackage.category_id == category_id)
    stmt = stmt.order_by(CareServicePackage.id)
    rows = db.execute(stmt).scalars().all()
    return [CarePackageOut.model_validate(r) for r in rows]


# ---------------- 预约 ----------------

def _to_out(app: CareAppointment) -> CareAppointmentOut:
    return CareAppointmentOut(
        id=app.id,
        appointment_no=app.appointment_no,
        user_id=app.user_id,
        user_nickname=app.user.nickname if app.user else "",
        user_pet_id=app.user_pet_id,
        pet_name=app.pet_name_snapshot,
        category_id=app.category_id,
        category_name=app.category_name_snapshot,
        package_id=app.package_id,
        package_name=app.package_name_snapshot,
        service_type=app.service_type,
        price_snapshot=app.price_snapshot,
        total_price=app.total_price,
        appointment_time=to_iso(app.appointment_time),
        check_in_date=app.check_in_date,
        check_out_date=app.check_out_date,
        contact_phone=app.contact_phone,
        note=app.note,
        status=app.status,
        review_comment=app.review_comment,
        reviewed_at=to_iso(app.reviewed_at),
        created_at=to_iso(app.created_at),
    )


def create_appointment(
    db: Session, user_id: int, data: CareAppointmentCreate
) -> CareAppointmentOut:
    repo = CareRepository(db)

    package = repo.get_package(data.package_id)
    if not package:
        raise NotFoundError("服务套餐不存在")
    if package.status != EnableStatus.ACTIVE.value:
        raise ConflictError("该套餐已停用，不可预约")
    category = repo.get_category(package.category_id)
    if not category or category.status != EnableStatus.ACTIVE.value:
        raise ConflictError("该分类已停用，不可预约")

    pet = db.get(UserPet, data.user_pet_id)
    if not pet or pet.user_id != user_id:
        raise NotFoundError("宠物档案不存在")
    if pet.status != UserPetStatus.ACTIVE.value:
        raise ConflictError("该宠物档案已停用，不可预约")

    service_type = category.service_type
    now = utcnow()

    if service_type == ServiceType.GROOMING.value:
        if data.appointment_time is None:
            raise ParamError("洗护服务需填写预约时间")
        appointment_time = to_utc_naive(data.appointment_time)
        if appointment_time <= now:
            raise ParamError("预约时间需晚于当前时间")
        check_in_date = None
        check_out_date = None
        total_price = package.price
    elif service_type == ServiceType.BOARDING.value:
        if data.check_in_date is None or data.check_out_date is None:
            raise ParamError("寄养服务需填写入住与离店日期")
        today = datetime.now(business_tz()).date()
        if data.check_in_date < today:
            raise ParamError("入住日期不能早于今天")
        if data.check_out_date <= data.check_in_date:
            raise ParamError("离店日期须晚于入住日期")
        days = (data.check_out_date - data.check_in_date).days
        total_price = package.price * days
        appointment_time = None
        check_in_date = data.check_in_date
        check_out_date = data.check_out_date
    else:
        raise ParamError("未知的服务类型")

    app = CareAppointment(
        appointment_no=gen_no("C"),
        user_id=user_id,
        user_pet_id=pet.id,
        category_id=category.id,
        package_id=package.id,
        service_type=service_type,
        pet_name_snapshot=pet.name,
        category_name_snapshot=category.name,
        package_name_snapshot=package.name,
        price_snapshot=package.price,
        total_price=total_price,
        appointment_time=appointment_time,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        contact_phone=data.contact_phone,
        note=data.note,
        status=CareAppointmentStatus.PENDING_CONFIRMATION.value,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return _to_out(app)


def list_my_appointments(db: Session, user_id: int) -> list[CareAppointmentOut]:
    stmt = (
        select(CareAppointment)
        .where(CareAppointment.user_id == user_id)
        .order_by(CareAppointment.id.desc())
    )
    rows = db.execute(stmt).scalars().all()
    return [_to_out(a) for a in rows]


def get_my_appointment(
    db: Session, user_id: int, appointment_id: int
) -> CareAppointmentOut:
    app = CareRepository(db).get_appointment(appointment_id)
    if not app or app.user_id != user_id:
        raise NotFoundError("预约不存在")
    return _to_out(app)


def cancel_appointment(
    db: Session, user_id: int, appointment_id: int
) -> CareAppointmentOut:
    app = CareRepository(db).get_appointment_for_update(appointment_id)
    if not app or app.user_id != user_id:
        raise NotFoundError("预约不存在")
    if app.status != CareAppointmentStatus.PENDING_CONFIRMATION.value:
        raise ConflictError("仅待确认的预约可取消")
    app.status = CareAppointmentStatus.CANCELLED.value
    db.commit()
    return _to_out(app)


def list_admin_appointments(
    db: Session,
    page: int,
    page_size: int,
    status: str | None = None,
    service_type: str | None = None,
    keyword: str | None = None,
) -> PageResult:
    stmt = select(CareAppointment)
    if status:
        stmt = stmt.where(CareAppointment.status == status)
    if service_type:
        stmt = stmt.where(CareAppointment.service_type == service_type)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                CareAppointment.appointment_no.like(like),
                CareAppointment.pet_name_snapshot.like(like),
                CareAppointment.contact_phone.like(like),
            )
        )
    stmt = stmt.order_by(CareAppointment.id.desc())

    page, page_size = normalize_page(page, page_size)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.limit(page_size).offset((page - 1) * page_size)).scalars().all()
    return PageResult(
        items=[_to_out(a) for a in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


def confirm_appointment(
    db: Session, admin: User, appointment_id: int
) -> CareAppointmentOut:
    app = CareRepository(db).get_appointment_for_update(appointment_id)
    if not app:
        raise NotFoundError("预约不存在")
    if app.status != CareAppointmentStatus.PENDING_CONFIRMATION.value:
        raise ConflictError("该预约已被处理，无法重复操作")
    app.status = CareAppointmentStatus.CONFIRMED.value
    app.reviewed_at = utcnow()
    db.commit()
    return _to_out(app)


def reject_appointment(
    db: Session, admin: User, appointment_id: int, comment: str
) -> CareAppointmentOut:
    app = CareRepository(db).get_appointment_for_update(appointment_id)
    if not app:
        raise NotFoundError("预约不存在")
    if app.status != CareAppointmentStatus.PENDING_CONFIRMATION.value:
        raise ConflictError("该预约已被处理，无法重复操作")
    app.status = CareAppointmentStatus.REJECTED.value
    app.review_comment = comment
    app.reviewed_at = utcnow()
    db.commit()
    return _to_out(app)


def complete_appointment(
    db: Session, admin: User, appointment_id: int
) -> CareAppointmentOut:
    app = CareRepository(db).get_appointment_for_update(appointment_id)
    if not app:
        raise NotFoundError("预约不存在")
    if app.status != CareAppointmentStatus.CONFIRMED.value:
        raise ConflictError("仅已确认的预约可标记完成")
    app.status = CareAppointmentStatus.COMPLETED.value
    db.commit()
    return _to_out(app)


# ---------------- 管理端资源维护 ----------------

def _require_category(db: Session, category_id: int) -> CareServiceCategory:
    cat = CareRepository(db).get_category(category_id)
    if not cat:
        raise NotFoundError("服务分类不存在")
    return cat


def _require_package(db: Session, package_id: int) -> CareServicePackage:
    pkg = CareRepository(db).get_package(package_id)
    if not pkg:
        raise NotFoundError("服务套餐不存在")
    return pkg


# 分类

def list_admin_categories(db: Session) -> list[CareCategoryOut]:
    stmt = select(CareServiceCategory).order_by(CareServiceCategory.sort, CareServiceCategory.id)
    return [CareCategoryOut.model_validate(r) for r in db.execute(stmt).scalars().all()]


def create_category(db: Session, data: CareCategoryCreate) -> CareCategoryOut:
    cat = CareServiceCategory(
        name=data.name,
        service_type=data.service_type.value,
        description=data.description,
        sort=data.sort,
        status=data.status.value,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return CareCategoryOut.model_validate(cat)


def update_category(
    db: Session, category_id: int, data: CareCategoryUpdate
) -> CareCategoryOut:
    cat = _require_category(db, category_id)
    payload = data.model_dump(exclude_unset=True)
    if "service_type" in payload:
        payload["service_type"] = payload["service_type"].value
    if "status" in payload:
        payload["status"] = payload["status"].value
    for k, v in payload.items():
        setattr(cat, k, v)
    db.commit()
    return CareCategoryOut.model_validate(cat)


def delete_category(db: Session, category_id: int) -> None:
    cat = _require_category(db, category_id)
    repo = CareRepository(db)
    if repo.count_packages_for_category(category_id) > 0:
        raise ConflictError("该分类下存在套餐，请先停用或迁移套餐")
    db.delete(cat)
    db.commit()


# 套餐

def list_admin_packages(db: Session, category_id: int | None = None) -> list[CarePackageOut]:
    stmt = select(CareServicePackage)
    if category_id:
        stmt = stmt.where(CareServicePackage.category_id == category_id)
    stmt = stmt.order_by(CareServicePackage.id)
    return [CarePackageOut.model_validate(r) for r in db.execute(stmt).scalars().all()]


def create_package(db: Session, data: CarePackageCreate) -> CarePackageOut:
    _require_category(db, data.category_id)
    pkg = CareServicePackage(
        category_id=data.category_id,
        name=data.name,
        description=data.description,
        price=data.price,
        duration_minutes=data.duration_minutes,
        status=data.status.value,
    )
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return CarePackageOut.model_validate(pkg)


def update_package(
    db: Session, package_id: int, data: CarePackageUpdate
) -> CarePackageOut:
    pkg = _require_package(db, package_id)
    payload = data.model_dump(exclude_unset=True)
    if "category_id" in payload:
        _require_category(db, payload["category_id"])
    if "status" in payload:
        payload["status"] = payload["status"].value
    for k, v in payload.items():
        setattr(pkg, k, v)
    db.commit()
    return CarePackageOut.model_validate(pkg)


def delete_package(db: Session, package_id: int) -> None:
    pkg = _require_package(db, package_id)
    repo = CareRepository(db)
    if repo.count_appointments_for_package(package_id) > 0:
        raise ConflictError("该套餐已被预约引用，请停用而非删除")
    db.delete(pkg)
    db.commit()
