"""医疗预约业务：公开查询、预约（排班容量事务）、管理端资源维护与预约处理。"""
from datetime import date, time

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.common.enums import (
    EnableStatus,
    MedicalAppointmentStatus,
    NotificationBusinessType,
    UserPetStatus,
)
from app.common.pagination import PageResult, normalize_page
from app.core.exceptions import ConflictError, NotFoundError, ParamError
from app.models.medical import (
    DoctorSchedule,
    MedicalAppointment,
    MedicalDoctor,
    MedicalLocation,
    MedicalService,
)
from app.models.pet import UserPet
from app.models.user import User
from app.repositories.medical import MedicalRepository
from app.schemas.medical import (
    DoctorScheduleCreate,
    DoctorScheduleOut,
    DoctorScheduleUpdate,
    MedicalAppointmentCreate,
    MedicalAppointmentOut,
    MedicalDoctorCreate,
    MedicalDoctorOut,
    MedicalDoctorUpdate,
    MedicalLocationCreate,
    MedicalLocationOut,
    MedicalLocationUpdate,
    MedicalServiceCreate,
    MedicalServiceOut,
    MedicalServiceUpdate,
)
from app.services import notification as notification_service
from app.utils.order_no import gen_no
from app.utils.time import combine_business_time, to_iso, utcnow


# ---------------- 公开查询 ----------------

def list_locations(db: Session) -> list[MedicalLocationOut]:
    stmt = (
        select(MedicalLocation)
        .where(MedicalLocation.status == EnableStatus.ACTIVE.value)
        .order_by(MedicalLocation.id)
    )
    rows = db.execute(stmt).scalars().all()
    return [MedicalLocationOut.model_validate(r) for r in rows]


def list_doctors(db: Session, location_id: int | None = None) -> list[MedicalDoctorOut]:
    stmt = select(MedicalDoctor).where(
        MedicalDoctor.status == EnableStatus.ACTIVE.value
    )
    if location_id:
        stmt = stmt.where(MedicalDoctor.location_id == location_id)
    stmt = stmt.order_by(MedicalDoctor.id)
    rows = db.execute(stmt).scalars().all()
    return [MedicalDoctorOut.model_validate(r) for r in rows]


def list_services(db: Session) -> list[MedicalServiceOut]:
    stmt = (
        select(MedicalService)
        .where(MedicalService.status == EnableStatus.ACTIVE.value)
        .order_by(MedicalService.id)
    )
    rows = db.execute(stmt).scalars().all()
    return [MedicalServiceOut.model_validate(r) for r in rows]


def _to_schedule_out(s: DoctorSchedule) -> DoctorScheduleOut:
    return DoctorScheduleOut(
        id=s.id,
        doctor_id=s.doctor_id,
        location_id=s.location_id,
        schedule_date=s.schedule_date,
        start_time=s.start_time,
        end_time=s.end_time,
        capacity=s.capacity,
        booked_count=s.booked_count,
        status=s.status,
        remaining=s.capacity - s.booked_count,
    )


def list_schedules(
    db: Session,
    doctor_id: int | None = None,
    location_id: int | None = None,
    schedule_date: date | None = None,
) -> list[DoctorScheduleOut]:
    """可预约时段：仅启用、未满额、未过期。"""
    stmt = select(DoctorSchedule).where(
        DoctorSchedule.status == EnableStatus.ACTIVE.value,
        DoctorSchedule.booked_count < DoctorSchedule.capacity,
    )
    if doctor_id:
        stmt = stmt.where(DoctorSchedule.doctor_id == doctor_id)
    if location_id:
        stmt = stmt.where(DoctorSchedule.location_id == location_id)
    if schedule_date:
        stmt = stmt.where(DoctorSchedule.schedule_date == schedule_date)
    stmt = stmt.order_by(DoctorSchedule.schedule_date, DoctorSchedule.start_time)
    rows = db.execute(stmt).scalars().all()

    now = utcnow()
    result: list[DoctorScheduleOut] = []
    for s in rows:
        if combine_business_time(s.schedule_date, s.end_time) <= now:
            continue  # 时段已过期，不展示
        result.append(_to_schedule_out(s))
    return result


# ---------------- 预约 ----------------

def _to_appointment_out(app: MedicalAppointment) -> MedicalAppointmentOut:
    schedule = app.schedule
    return MedicalAppointmentOut(
        id=app.id,
        appointment_no=app.appointment_no,
        user_id=app.user_id,
        user_nickname=app.user.nickname if app.user else "",
        user_pet_id=app.user_pet_id,
        pet_name=app.pet_name_snapshot,
        location_id=app.location_id,
        location_name=app.location.name if app.location else "",
        doctor_id=app.doctor_id,
        doctor_name=app.doctor.name if app.doctor else "",
        service_id=app.service_id,
        service_name=app.service_name_snapshot,
        schedule_id=app.schedule_id,
        schedule_date=schedule.schedule_date if schedule else None,
        start_time=schedule.start_time if schedule else None,
        end_time=schedule.end_time if schedule else None,
        appointment_time=to_iso(app.appointment_time),
        symptom_note=app.symptom_note,
        contact_phone=app.contact_phone,
        status=app.status,
        review_comment=app.review_comment,
        reviewed_at=to_iso(app.reviewed_at),
        created_at=to_iso(app.created_at),
    )


def create_appointment(
    db: Session, user_id: int, data: MedicalAppointmentCreate
) -> MedicalAppointmentOut:
    repo = MedicalRepository(db)

    schedule = repo.get_schedule_for_update(data.schedule_id)
    if not schedule:
        raise NotFoundError("排班时段不存在")
    if schedule.status != EnableStatus.ACTIVE.value:
        raise ConflictError("该时段已关闭，不可预约")
    if combine_business_time(schedule.schedule_date, schedule.end_time) <= utcnow():
        raise ConflictError("该时段已过期，不可预约")
    if schedule.booked_count >= schedule.capacity:
        raise ConflictError("该时段已约满")

    if repo.has_active_appointment(user_id, data.schedule_id):
        raise ConflictError("你已预约过该时段，请勿重复预约")

    pet = db.get(UserPet, data.user_pet_id)
    if not pet or pet.user_id != user_id:
        raise NotFoundError("宠物档案不存在")
    if pet.status != UserPetStatus.ACTIVE.value:
        raise ConflictError("该宠物档案已停用，不可预约")

    service = repo.get_service(data.service_id)
    if not service:
        raise NotFoundError("医疗项目不存在")
    if service.status != EnableStatus.ACTIVE.value:
        raise ConflictError("该医疗项目已停用")

    doctor = repo.get_doctor(schedule.doctor_id)
    if not doctor or doctor.status != EnableStatus.ACTIVE.value:
        raise ConflictError("该医生暂不可预约")

    schedule.booked_count += 1
    app = MedicalAppointment(
        appointment_no=gen_no("M"),
        user_id=user_id,
        user_pet_id=pet.id,
        location_id=schedule.location_id,
        doctor_id=schedule.doctor_id,
        service_id=service.id,
        schedule_id=schedule.id,
        pet_name_snapshot=pet.name,
        service_name_snapshot=service.name,
        appointment_time=combine_business_time(
            schedule.schedule_date, schedule.start_time
        ),
        symptom_note=data.symptom_note,
        contact_phone=data.contact_phone,
        status=MedicalAppointmentStatus.PENDING_CONFIRMATION.value,
    )
    db.add(app)
    db.flush()
    notification_service.create_notification(
        db,
        NotificationBusinessType.MEDICAL_APPOINTMENT.value,
        app.id,
        "收到新的医疗预约",
        f"{pet.name} 预约「{service.name}」",
    )
    db.commit()
    db.refresh(app)
    notification_service.push_new_business(
        NotificationBusinessType.MEDICAL_APPOINTMENT.value, app.id, "收到新的医疗预约"
    )
    return _to_appointment_out(app)


def list_my_appointments(db: Session, user_id: int) -> list[MedicalAppointmentOut]:
    stmt = (
        select(MedicalAppointment)
        .where(MedicalAppointment.user_id == user_id)
        .order_by(MedicalAppointment.id.desc())
    )
    rows = db.execute(stmt).scalars().all()
    return [_to_appointment_out(a) for a in rows]


def get_my_appointment(
    db: Session, user_id: int, appointment_id: int
) -> MedicalAppointmentOut:
    app = MedicalRepository(db).get_appointment(appointment_id)
    if not app or app.user_id != user_id:
        raise NotFoundError("预约不存在")
    return _to_appointment_out(app)


def cancel_appointment(
    db: Session, user_id: int, appointment_id: int
) -> MedicalAppointmentOut:
    repo = MedicalRepository(db)
    app = repo.get_appointment_for_update(appointment_id)
    if not app or app.user_id != user_id:
        raise NotFoundError("预约不存在")
    if app.status != MedicalAppointmentStatus.PENDING_CONFIRMATION.value:
        raise ConflictError("仅待确认的预约可取消")

    _release_slot(repo, app.schedule_id)
    app.status = MedicalAppointmentStatus.CANCELLED.value
    db.commit()
    return _to_appointment_out(app)


def _release_slot(repo: MedicalRepository, schedule_id: int) -> None:
    schedule = repo.get_schedule_for_update(schedule_id)
    if schedule and schedule.booked_count > 0:
        schedule.booked_count -= 1


def list_admin_appointments(
    db: Session,
    page: int,
    page_size: int,
    status: str | None = None,
    doctor_id: int | None = None,
    location_id: int | None = None,
    keyword: str | None = None,
) -> PageResult:
    stmt = select(MedicalAppointment)
    if status:
        stmt = stmt.where(MedicalAppointment.status == status)
    if doctor_id:
        stmt = stmt.where(MedicalAppointment.doctor_id == doctor_id)
    if location_id:
        stmt = stmt.where(MedicalAppointment.location_id == location_id)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                MedicalAppointment.appointment_no.like(like),
                MedicalAppointment.pet_name_snapshot.like(like),
                MedicalAppointment.contact_phone.like(like),
            )
        )
    stmt = stmt.order_by(MedicalAppointment.id.desc())

    page, page_size = normalize_page(page, page_size)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.limit(page_size).offset((page - 1) * page_size)).scalars().all()
    return PageResult(
        items=[_to_appointment_out(a) for a in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


def confirm_appointment(
    db: Session, admin: User, appointment_id: int
) -> MedicalAppointmentOut:
    app = MedicalRepository(db).get_appointment_for_update(appointment_id)
    if not app:
        raise NotFoundError("预约不存在")
    if app.status != MedicalAppointmentStatus.PENDING_CONFIRMATION.value:
        raise ConflictError("该预约已被处理，无法重复操作")

    app.status = MedicalAppointmentStatus.CONFIRMED.value
    app.reviewed_at = utcnow()
    notification_service.mark_business_read(
        db, NotificationBusinessType.MEDICAL_APPOINTMENT.value, app.id
    )
    db.commit()
    return _to_appointment_out(app)


def reject_appointment(
    db: Session, admin: User, appointment_id: int, comment: str
) -> MedicalAppointmentOut:
    repo = MedicalRepository(db)
    app = repo.get_appointment_for_update(appointment_id)
    if not app:
        raise NotFoundError("预约不存在")
    if app.status != MedicalAppointmentStatus.PENDING_CONFIRMATION.value:
        raise ConflictError("该预约已被处理，无法重复操作")

    _release_slot(repo, app.schedule_id)
    app.status = MedicalAppointmentStatus.REJECTED.value
    app.review_comment = comment
    app.reviewed_at = utcnow()
    notification_service.mark_business_read(
        db, NotificationBusinessType.MEDICAL_APPOINTMENT.value, app.id
    )
    db.commit()
    return _to_appointment_out(app)


def complete_appointment(
    db: Session, admin: User, appointment_id: int
) -> MedicalAppointmentOut:
    app = MedicalRepository(db).get_appointment_for_update(appointment_id)
    if not app:
        raise NotFoundError("预约不存在")
    if app.status != MedicalAppointmentStatus.CONFIRMED.value:
        raise ConflictError("仅已确认的预约可标记完成")

    app.status = MedicalAppointmentStatus.COMPLETED.value
    notification_service.mark_business_read(
        db, NotificationBusinessType.MEDICAL_APPOINTMENT.value, app.id
    )
    db.commit()
    return _to_appointment_out(app)


# ---------------- 管理端资源维护 ----------------

def _require_location(db: Session, location_id: int) -> MedicalLocation:
    loc = MedicalRepository(db).get_location(location_id)
    if not loc:
        raise NotFoundError("医疗点不存在")
    return loc


def _require_doctor(db: Session, doctor_id: int) -> MedicalDoctor:
    doc = MedicalRepository(db).get_doctor(doctor_id)
    if not doc:
        raise NotFoundError("医生不存在")
    return doc


def _require_service(db: Session, service_id: int) -> MedicalService:
    svc = MedicalRepository(db).get_service(service_id)
    if not svc:
        raise NotFoundError("医疗项目不存在")
    return svc


# 医疗点

def list_admin_locations(db: Session) -> list[MedicalLocationOut]:
    stmt = select(MedicalLocation).order_by(MedicalLocation.id)
    return [MedicalLocationOut.model_validate(r) for r in db.execute(stmt).scalars().all()]


def create_location(db: Session, data: MedicalLocationCreate) -> MedicalLocationOut:
    loc = MedicalLocation(
        name=data.name,
        address=data.address,
        phone=data.phone,
        description=data.description,
        status=data.status.value,
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return MedicalLocationOut.model_validate(loc)


def update_location(
    db: Session, location_id: int, data: MedicalLocationUpdate
) -> MedicalLocationOut:
    loc = _require_location(db, location_id)
    payload = data.model_dump(exclude_unset=True)
    if "status" in payload:
        payload["status"] = payload["status"].value
    for k, v in payload.items():
        setattr(loc, k, v)
    db.commit()
    return MedicalLocationOut.model_validate(loc)


def delete_location(db: Session, location_id: int) -> None:
    loc = _require_location(db, location_id)
    repo = MedicalRepository(db)
    if repo.count_doctors_for_location(location_id) > 0:
        raise ConflictError("该医疗点下存在医生，请先停用或迁移医生")
    db.delete(loc)
    db.commit()


# 医生

def list_admin_doctors(
    db: Session, location_id: int | None = None
) -> list[MedicalDoctorOut]:
    stmt = select(MedicalDoctor)
    if location_id:
        stmt = stmt.where(MedicalDoctor.location_id == location_id)
    stmt = stmt.order_by(MedicalDoctor.id)
    return [MedicalDoctorOut.model_validate(r) for r in db.execute(stmt).scalars().all()]


def create_doctor(db: Session, data: MedicalDoctorCreate) -> MedicalDoctorOut:
    _require_location(db, data.location_id)
    doc = MedicalDoctor(
        location_id=data.location_id,
        name=data.name,
        avatar_url=data.avatar_url,
        title=data.title,
        specialty=data.specialty,
        status=data.status.value,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return MedicalDoctorOut.model_validate(doc)


def update_doctor(
    db: Session, doctor_id: int, data: MedicalDoctorUpdate
) -> MedicalDoctorOut:
    doc = _require_doctor(db, doctor_id)
    payload = data.model_dump(exclude_unset=True)
    if "location_id" in payload:
        _require_location(db, payload["location_id"])
    if "status" in payload:
        payload["status"] = payload["status"].value
    for k, v in payload.items():
        setattr(doc, k, v)
    db.commit()
    return MedicalDoctorOut.model_validate(doc)


def delete_doctor(db: Session, doctor_id: int) -> None:
    doc = _require_doctor(db, doctor_id)
    repo = MedicalRepository(db)
    if repo.count_schedules_for_doctor(doctor_id) > 0:
        raise ConflictError("该医生存在排班，请先停用或清理排班")
    db.delete(doc)
    db.commit()


# 医疗项目

def list_admin_services(db: Session) -> list[MedicalServiceOut]:
    stmt = select(MedicalService).order_by(MedicalService.id)
    return [MedicalServiceOut.model_validate(r) for r in db.execute(stmt).scalars().all()]


def create_service(db: Session, data: MedicalServiceCreate) -> MedicalServiceOut:
    svc = MedicalService(
        name=data.name,
        description=data.description,
        reference_price=data.reference_price,
        duration_minutes=data.duration_minutes,
        status=data.status.value,
    )
    db.add(svc)
    db.commit()
    db.refresh(svc)
    return MedicalServiceOut.model_validate(svc)


def update_service(
    db: Session, service_id: int, data: MedicalServiceUpdate
) -> MedicalServiceOut:
    svc = _require_service(db, service_id)
    payload = data.model_dump(exclude_unset=True)
    if "status" in payload:
        payload["status"] = payload["status"].value
    for k, v in payload.items():
        setattr(svc, k, v)
    db.commit()
    return MedicalServiceOut.model_validate(svc)


def delete_service(db: Session, service_id: int) -> None:
    svc = _require_service(db, service_id)
    repo = MedicalRepository(db)
    if repo.count_appointments_for_service(service_id) > 0:
        raise ConflictError("该医疗项目已被预约引用，请停用而非删除")
    db.delete(svc)
    db.commit()


# 排班

def _has_overlap(
    db: Session,
    doctor_id: int,
    day: date,
    start: time,
    end: time,
    exclude_id: int | None = None,
) -> bool:
    for s in MedicalRepository(db).list_doctor_schedules_on(doctor_id, day):
        if exclude_id is not None and s.id == exclude_id:
            continue
        if start < s.end_time and s.start_time < end:
            return True
    return False


def list_admin_schedules(
    db: Session, doctor_id: int | None = None, schedule_date: date | None = None
) -> list[DoctorScheduleOut]:
    stmt = select(DoctorSchedule)
    if doctor_id:
        stmt = stmt.where(DoctorSchedule.doctor_id == doctor_id)
    if schedule_date:
        stmt = stmt.where(DoctorSchedule.schedule_date == schedule_date)
    stmt = stmt.order_by(DoctorSchedule.schedule_date, DoctorSchedule.start_time)
    return [_to_schedule_out(s) for s in db.execute(stmt).scalars().all()]


def create_schedule(db: Session, data: DoctorScheduleCreate) -> DoctorScheduleOut:
    doctor = _require_doctor(db, data.doctor_id)
    if doctor.location_id != data.location_id:
        raise ParamError("医生不属于该医疗点")
    if data.start_time >= data.end_time:
        raise ParamError("结束时间必须晚于开始时间")
    if _has_overlap(db, data.doctor_id, data.schedule_date, data.start_time, data.end_time):
        raise ConflictError("该医生当天存在时间重叠的排班")

    s = DoctorSchedule(
        doctor_id=data.doctor_id,
        location_id=data.location_id,
        schedule_date=data.schedule_date,
        start_time=data.start_time,
        end_time=data.end_time,
        capacity=data.capacity,
        booked_count=0,
        status=data.status.value,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return _to_schedule_out(s)


def update_schedule(
    db: Session, schedule_id: int, data: DoctorScheduleUpdate
) -> DoctorScheduleOut:
    s = MedicalRepository(db).get_schedule(schedule_id)
    if not s:
        raise NotFoundError("排班不存在")
    payload = data.model_dump(exclude_unset=True)

    new_doctor_id = payload.get("doctor_id", s.doctor_id)
    new_location_id = payload.get("location_id", s.location_id)
    new_date = payload.get("schedule_date", s.schedule_date)
    new_start = payload.get("start_time", s.start_time)
    new_end = payload.get("end_time", s.end_time)
    new_capacity = payload.get("capacity", s.capacity)

    if "doctor_id" in payload or "location_id" in payload:
        doctor = _require_doctor(db, new_doctor_id)
        if doctor.location_id != new_location_id:
            raise ParamError("医生不属于该医疗点")

    if new_start >= new_end:
        raise ParamError("结束时间必须晚于开始时间")
    if new_capacity < s.booked_count:
        raise ConflictError("容量不能小于已预约数")
    if _has_overlap(db, new_doctor_id, new_date, new_start, new_end, exclude_id=s.id):
        raise ConflictError("该医生当天存在时间重叠的排班")

    if "status" in payload:
        payload["status"] = payload["status"].value
    for k, v in payload.items():
        setattr(s, k, v)
    db.commit()
    return _to_schedule_out(s)


def delete_schedule(db: Session, schedule_id: int) -> None:
    s = MedicalRepository(db).get_schedule(schedule_id)
    if not s:
        raise NotFoundError("排班不存在")
    repo = MedicalRepository(db)
    if repo.count_unfinished_appointments_for_schedule(schedule_id) > 0:
        raise ConflictError("该排班存在未完成预约，只能停用，不可删除")
    db.delete(s)
    db.commit()
