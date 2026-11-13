"""管理端商城接口：分类/商品 CRUD + 订单发货/完成。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.pagination import PageResult
from app.common.response import ApiResponse
from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.user import User
from app.schemas.mall import (
    OrderOut,
    ProductCategoryCreate,
    ProductCategoryOut,
    ProductCategoryUpdate,
    ProductCreate,
    ProductOut,
    ProductUpdate,
)
from app.services import mall as mall_service

router = APIRouter(prefix="/mall", tags=["商城资源管理"])


# ---------------- 分类 ----------------

@router.get("/categories", response_model=ApiResponse[list[ProductCategoryOut]])
def list_categories(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return ApiResponse(data=mall_service.list_admin_categories(db))


@router.post("/categories", response_model=ApiResponse[ProductCategoryOut])
def create_category(
    data: ProductCategoryCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=mall_service.create_category(db, data))


@router.put("/categories/{category_id}", response_model=ApiResponse[ProductCategoryOut])
def update_category(
    category_id: int,
    data: ProductCategoryUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=mall_service.update_category(db, category_id, data))


@router.delete("/categories/{category_id}", response_model=ApiResponse)
def delete_category(
    category_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    mall_service.delete_category(db, category_id)
    return ApiResponse()


# ---------------- 商品 ----------------

@router.get("/products", response_model=ApiResponse[list[ProductOut]])
def list_products(
    category_id: int | None = Query(None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=mall_service.list_admin_products(db, category_id))


@router.post("/products", response_model=ApiResponse[ProductOut])
def create_product(
    data: ProductCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=mall_service.create_product(db, data))


@router.put("/products/{product_id}", response_model=ApiResponse[ProductOut])
def update_product(
    product_id: int,
    data: ProductUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=mall_service.update_product(db, product_id, data))


@router.delete("/products/{product_id}", response_model=ApiResponse)
def delete_product(
    product_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    mall_service.delete_product(db, product_id)
    return ApiResponse()


# ---------------- 订单处理 ----------------

@router.get("/orders", response_model=ApiResponse[PageResult])
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = Query(None),
    keyword: str | None = Query(None, max_length=50),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    result = mall_service.list_admin_orders(db, page, page_size, status, keyword)
    return ApiResponse(data=result)


@router.post("/orders/{order_id}/ship", response_model=ApiResponse[OrderOut])
def ship_order(
    order_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=mall_service.ship_order(db, admin, order_id))


@router.post("/orders/{order_id}/complete", response_model=ApiResponse[OrderOut])
def complete_order(
    order_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=mall_service.complete_order(db, admin, order_id))
