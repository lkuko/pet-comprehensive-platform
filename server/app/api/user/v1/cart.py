"""用户端购物车接口：列表、加购、改数量、删除、清空。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import ApiResponse
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.mall import CartItemAdd, CartItemOut, CartItemUpdate
from app.services import mall as mall_service

router = APIRouter(prefix="/cart", tags=["购物车"])


@router.get("", response_model=ApiResponse[list[CartItemOut]])
def list_cart(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ApiResponse(data=mall_service.list_cart(db, user.id))


@router.post("", response_model=ApiResponse[CartItemOut])
def add_to_cart(
    data: CartItemAdd,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=mall_service.add_to_cart(db, user.id, data))


@router.put("/{product_id}", response_model=ApiResponse[list[CartItemOut]])
def update_cart_item(
    product_id: int,
    data: CartItemUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=mall_service.update_cart_item(db, user.id, product_id, data))


@router.delete("/{product_id}", response_model=ApiResponse[list[CartItemOut]])
def remove_cart_item(
    product_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=mall_service.remove_cart_item(db, user.id, product_id))


@router.delete("", response_model=ApiResponse)
def clear_cart(user: User = Depends(get_current_user)):
    mall_service.clear_cart(user.id)
    return ApiResponse()
