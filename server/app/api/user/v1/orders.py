"""用户端订单接口：下单、列表、详情、支付、取消。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import ApiResponse
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.mall import CheckoutCreate, OrderOut
from app.services import mall as mall_service

router = APIRouter(prefix="/orders", tags=["我的订单"])


@router.post("", response_model=ApiResponse[OrderOut])
def checkout(
    data: CheckoutCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=mall_service.checkout(db, user.id, data))


@router.get("", response_model=ApiResponse[list[OrderOut]])
def list_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ApiResponse(data=mall_service.list_my_orders(db, user.id))


@router.get("/{order_id}", response_model=ApiResponse[OrderOut])
def get_order(
    order_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=mall_service.get_my_order(db, user.id, order_id))


@router.post("/{order_id}/pay", response_model=ApiResponse[OrderOut])
def pay_order(
    order_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=mall_service.pay_order(db, user.id, order_id))


@router.post("/{order_id}/cancel", response_model=ApiResponse[OrderOut])
def cancel_order(
    order_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=mall_service.cancel_order(db, user.id, order_id))


@router.post("/{order_id}/confirm-receipt", response_model=ApiResponse[OrderOut])
def confirm_receipt(
    order_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=mall_service.confirm_receipt(db, user.id, order_id))
