"""公开端商城接口：商品分类与商品列表（游客可访问）。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.pagination import PageResult
from app.common.response import ApiResponse
from app.core.database import get_db
from app.schemas.mall import ProductCategoryOut, ProductOut
from app.services import mall as mall_service

router = APIRouter(prefix="/mall", tags=["商城"])


@router.get("/categories", response_model=ApiResponse[list[ProductCategoryOut]])
def list_categories(db: Session = Depends(get_db)):
    return ApiResponse(data=mall_service.list_categories(db))


@router.get("/products", response_model=ApiResponse[PageResult])
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category_id: int | None = Query(None),
    keyword: str | None = Query(None, max_length=50),
    db: Session = Depends(get_db),
):
    return ApiResponse(
        data=mall_service.list_products(db, page, page_size, category_id, keyword)
    )


@router.get("/products/{product_id}", response_model=ApiResponse[ProductOut])
def get_product(product_id: int, db: Session = Depends(get_db)):
    return ApiResponse(data=mall_service.get_product(db, product_id))
