"""管理端工作台接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import ApiResponse
from app.core.deps import get_current_admin, get_db
from app.models.user import User
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/dashboard", tags=["管理端-工作台"])


@router.get("/summary", response_model=ApiResponse[dict])
def summary(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=dashboard_service.get_summary(db))
