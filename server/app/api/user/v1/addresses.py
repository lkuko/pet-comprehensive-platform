"""用户端收货地址接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import ApiResponse
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.mall import AddressCreate, AddressOut, AddressUpdate
from app.services import mall as mall_service

router = APIRouter(prefix="/addresses", tags=["收货地址"])


@router.get("", response_model=ApiResponse[list[AddressOut]])
def list_addresses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ApiResponse(data=mall_service.list_addresses(db, user.id))


@router.post("", response_model=ApiResponse[AddressOut])
def create_address(
    data: AddressCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=mall_service.create_address(db, user.id, data))


@router.put("/{address_id}", response_model=ApiResponse[AddressOut])
def update_address(
    address_id: int,
    data: AddressUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=mall_service.update_address(db, user.id, address_id, data))


@router.delete("/{address_id}", response_model=ApiResponse)
def delete_address(
    address_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mall_service.delete_address(db, user.id, address_id)
    return ApiResponse()


@router.post("/{address_id}/default", response_model=ApiResponse[AddressOut])
def set_default_address(
    address_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=mall_service.set_default_address(db, user.id, address_id))
