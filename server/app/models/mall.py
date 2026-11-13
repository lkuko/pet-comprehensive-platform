"""商城相关模型（宠物用品）。

表：product_categories（商品分类）、products（商品 SPU）、
    orders（订单）、order_items（订单明细）。

订单与明细对商品名、封面、单价做快照，商品后续调价/下架/删除不影响历史订单。
库存扣减在 checkout 事务内通过 SELECT FOR UPDATE 完成，防止超卖。
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PkType, TimestampMixin


class ProductCategory(Base, TimestampMixin):
    """商品分类（狗粮、猫砂、玩具、洗护用品等）。"""

    __tablename__ = "product_categories"

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)


class Product(Base, TimestampMixin):
    """商品（SPU），含库存与销量。"""

    __tablename__ = "products"
    __table_args__ = (Index("ix_products_category_status", "category_id", "status"),)

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("product_categories.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sales: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)

    category: Mapped["ProductCategory"] = relationship(lazy="selectin")


class Order(Base, TimestampMixin):
    """订单（含收货信息、幂等键与状态机）。"""

    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_user_status", "user_id", "status"),
        UniqueConstraint("user_id", "idempotency_key", name="uq_orders_user_idem"),
    )

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING_PAYMENT", index=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    receiver_name: Mapped[str] = mapped_column(String(50), nullable=False)
    receiver_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    receiver_address: Mapped[str] = mapped_column(String(200), nullable=False)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(lazy="selectin")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="OrderItem.id",
    )


class OrderItem(Base):
    """订单明细（商品快照）。"""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )
    product_name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    product_cover_snapshot: Mapped[str | None] = mapped_column(String(500), nullable=True)
    unit_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    order: Mapped["Order"] = relationship(back_populates="items")


class UserAddress(Base, TimestampMixin):
    """用户收货地址。"""

    __tablename__ = "user_addresses"
    __table_args__ = (Index("ix_user_addresses_user", "user_id", "is_default"),)

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    receiver_name: Mapped[str] = mapped_column(String(50), nullable=False)
    receiver_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    province: Mapped[str | None] = mapped_column(String(50), nullable=True)
    city: Mapped[str | None] = mapped_column(String(50), nullable=True)
    district: Mapped[str | None] = mapped_column(String(50), nullable=True)
    detail_address: Mapped[str] = mapped_column(String(200), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class InventoryLog(Base, TimestampMixin):
    """库存变更流水（每次库存变化必须写一条，扣减记负数、返还/增加记正数）。"""

    __tablename__ = "inventory_logs"
    __table_args__ = (Index("ix_inventory_logs_product", "product_id", "created_at"),)

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    change_type: Mapped[str] = mapped_column(String(20), nullable=False)
    change_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    before_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    after_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    related_order_no: Mapped[str | None] = mapped_column(String(40), nullable=True)
    operator_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    remark: Mapped[str | None] = mapped_column(String(200), nullable=True)
