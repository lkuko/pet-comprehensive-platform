"""管理端通知接口。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.pagination import PageResult
from app.common.response import ApiResponse, ok
from app.core.deps import get_current_admin, get_db
from app.models.user import User
from app.schemas.notification import NotificationOut
from app.services import notification as notification_service

router = APIRouter(prefix="/notifications", tags=["管理端-通知"])


@router.get("", response_model=ApiResponse[PageResult])
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    unread_only: bool = Query(False),
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(
        data=notification_service.list_notifications(db, page, page_size, unread_only)
    )


@router.get("/unread-count", response_model=ApiResponse[dict])
def get_unread_count(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data={"count": notification_service.unread_count(db)})


@router.post("/{notification_id}/read", response_model=ApiResponse[NotificationOut])
def mark_read(
    notification_id: int,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=notification_service.mark_read(db, notification_id))


@router.post("/read-all", response_model=ApiResponse[dict])
def mark_all_read(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data={"count": notification_service.mark_all_read(db)})
