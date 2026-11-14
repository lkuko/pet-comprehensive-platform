"""通知与业务提醒：创建/查询/已读 + 事务提交后的 WebSocket 推送。"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.pagination import PageResult, normalize_page
from app.core.exceptions import NotFoundError
from app.models.notification import AdminNotification
from app.schemas.notification import NotificationOut
from app.utils.time import to_iso, utcnow


def _to_out(n: AdminNotification) -> NotificationOut:
    return NotificationOut(
        id=n.id,
        business_type=n.business_type,
        business_id=n.business_id,
        title=n.title,
        content=n.content,
        is_read=n.is_read,
        read_at=to_iso(n.read_at),
        created_at=to_iso(n.created_at),
    )


def create_notification(
    db: Session,
    business_type: str,
    business_id: int,
    title: str,
    content: str | None = None,
) -> AdminNotification:
    """在业务事务内创建通知记录（随业务一起提交，保证通知不丢失）。

    调用方需在 commit 前调用本函数（仅 db.add，不提交）。
    """
    n = AdminNotification(
        business_type=business_type,
        business_id=business_id,
        title=title,
        content=content,
        is_read=False,
    )
    db.add(n)
    return n


def push_new_business(business_type: str, business_id: int, title: str) -> None:
    """业务事务提交后推送 WebSocket 提醒（失败仅记日志，不影响业务）。"""
    from app.websocket.manager import notification_manager

    notification_manager.broadcast_sync(
        {
            "event": "NEW_BUSINESS",
            "business_type": business_type,
            "business_id": business_id,
            "title": title,
            "created_at": to_iso(utcnow()),
        }
    )


def list_notifications(
    db: Session,
    page: int,
    page_size: int,
    unread_only: bool = False,
) -> PageResult:
    stmt = select(AdminNotification)
    if unread_only:
        stmt = stmt.where(AdminNotification.is_read.is_(False))
    stmt = stmt.order_by(AdminNotification.id.desc())

    page, page_size = normalize_page(page, page_size)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.limit(page_size).offset((page - 1) * page_size)).scalars().all()
    return PageResult(
        items=[_to_out(n) for n in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


def unread_count(db: Session) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(AdminNotification)
            .where(AdminNotification.is_read.is_(False))
        )
        or 0
    )


def mark_read(db: Session, notification_id: int) -> NotificationOut:
    n = db.get(AdminNotification, notification_id)
    if not n:
        raise NotFoundError("通知不存在")
    if not n.is_read:
        n.is_read = True
        n.read_at = utcnow()
        db.commit()
    return _to_out(n)


def mark_all_read(db: Session) -> int:
    """将全部未读通知标记为已读，返回本次标记数量。"""
    rows = db.execute(
        select(AdminNotification).where(AdminNotification.is_read.is_(False))
    ).scalars().all()
    now = utcnow()
    for n in rows:
        n.is_read = True
        n.read_at = now
    db.commit()
    return len(rows)
