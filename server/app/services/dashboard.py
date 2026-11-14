"""管理端工作台统计：真实来自 MySQL 聚合，不依赖缓存。"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums import (
    AdoptionApplicationStatus,
    CareAppointmentStatus,
    MedicalAppointmentStatus,
    OrderStatus,
    UserRole,
)
from app.models.care import CareAppointment
from app.models.medical import MedicalAppointment
from app.models.notification import AdminNotification
from app.models.pet import AdoptionApplication
from app.models.mall import Order
from app.models.user import User
from app.utils.time import to_iso


def get_summary(db: Session) -> dict:
    """工作台统计：核心待办数 + 用户数 + 最近业务动态。"""
    user_count = (
        db.scalar(select(func.count()).select_from(User).where(User.role == UserRole.USER.value))
        or 0
    )
    pending_adoption = (
        db.scalar(
            select(func.count())
            .select_from(AdoptionApplication)
            .where(AdoptionApplication.status == AdoptionApplicationStatus.PENDING.value)
        )
        or 0
    )
    pending_medical = (
        db.scalar(
            select(func.count())
            .select_from(MedicalAppointment)
            .where(MedicalAppointment.status == MedicalAppointmentStatus.PENDING_CONFIRMATION.value)
        )
        or 0
    )
    pending_care = (
        db.scalar(
            select(func.count())
            .select_from(CareAppointment)
            .where(CareAppointment.status == CareAppointmentStatus.PENDING_CONFIRMATION.value)
        )
        or 0
    )
    pending_ship = (
        db.scalar(
            select(func.count())
            .select_from(Order)
            .where(Order.status == OrderStatus.PAID.value)
        )
        or 0
    )

    unread = (
        db.scalar(
            select(func.count())
            .select_from(AdminNotification)
            .where(AdminNotification.is_read.is_(False))
        )
        or 0
    )

    # 最近业务动态：最近 8 条通知
    recent = [
        {
            "id": n.id,
            "business_type": n.business_type,
            "business_id": n.business_id,
            "title": n.title,
            "created_at": to_iso(n.created_at),
        }
        for n in db.execute(
            select(AdminNotification).order_by(AdminNotification.id.desc()).limit(8)
        ).scalars().all()
    ]

    return {
        "user_count": user_count,
        "pending_adoption": pending_adoption,
        "pending_medical": pending_medical,
        "pending_care": pending_care,
        "pending_ship": pending_ship,
        "unread_notifications": unread,
        "recent_business": recent,
    }
