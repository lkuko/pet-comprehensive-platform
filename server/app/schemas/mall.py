"""商城相关 Schema：商品分类、商品、购物车、订单。"""
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import EnableStatus


# ---------------- 商品分类 ----------------

class ProductCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str | None = None
    sort: int = Field(default=0, ge=0)
    status: EnableStatus = EnableStatus.ACTIVE


class ProductCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = None
    sort: int | None = Field(default=None, ge=0)
    status: EnableStatus | None = None


class ProductCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    sort: int
    status: str


# ---------------- 商品 ----------------

class ProductCreate(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=100)
    subtitle: str | None = Field(default=None, max_length=200)
    description: str | None = None
    cover_image: str | None = Field(default=None, max_length=500)
    price: Decimal = Field(default=0, ge=0, max_digits=10, decimal_places=2)
    stock: int = Field(default=0, ge=0)
    status: EnableStatus = EnableStatus.ACTIVE


class ProductUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    subtitle: str | None = Field(default=None, max_length=200)
    description: str | None = None
    cover_image: str | None = Field(default=None, max_length=500)
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    stock: int | None = Field(default=None, ge=0)
    status: EnableStatus | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    category_name: str | None = None
    name: str
    subtitle: str | None
    description: str | None
    cover_image: str | None
    price: Decimal
    stock: int
    sales: int
    status: str


# ---------------- 购物车 ----------------

class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(default=1, ge=0, le=999)


class CartItemOut(BaseModel):
    product_id: int
    name: str
    cover_image: str | None
    price: Decimal
    stock: int
    quantity: int
    subtotal: Decimal


# ---------------- 订单 ----------------

class CheckoutCreate(BaseModel):
    idempotency_key: str | None = Field(default=None, max_length=64)
    receiver_name: str = Field(min_length=1, max_length=50)
    receiver_phone: str = Field(min_length=1, max_length=20)
    receiver_address: str = Field(min_length=1, max_length=200)
    remark: str | None = None


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_cover: str | None
    unit_price: Decimal
    quantity: int
    subtotal: Decimal


class OrderOut(BaseModel):
    id: int
    order_no: str
    user_id: int
    user_nickname: str
    status: str
    total_amount: Decimal
    receiver_name: str
    receiver_phone: str
    receiver_address: str
    remark: str | None
    items: list[OrderItemOut] = []
    paid_at: str | None
    shipped_at: str | None
    completed_at: str | None
    cancelled_at: str | None
    closed_at: str | None
    created_at: str


# ---------------- 收货地址 ----------------

class AddressCreate(BaseModel):
    receiver_name: str = Field(min_length=1, max_length=50)
    receiver_phone: str = Field(min_length=1, max_length=20)
    province: str | None = Field(default=None, max_length=50)
    city: str | None = Field(default=None, max_length=50)
    district: str | None = Field(default=None, max_length=50)
    detail_address: str = Field(min_length=1, max_length=200)
    is_default: bool = False


class AddressUpdate(BaseModel):
    receiver_name: str | None = Field(default=None, min_length=1, max_length=50)
    receiver_phone: str | None = Field(default=None, min_length=1, max_length=20)
    province: str | None = Field(default=None, max_length=50)
    city: str | None = Field(default=None, max_length=50)
    district: str | None = Field(default=None, max_length=50)
    detail_address: str | None = Field(default=None, min_length=1, max_length=200)
    is_default: bool | None = None


class AddressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    receiver_name: str
    receiver_phone: str
    province: str | None
    city: str | None
    district: str | None
    detail_address: str
    is_default: bool
