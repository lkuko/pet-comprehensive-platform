"""商城业务：公开查询、购物车（Redis）、下单锁库存、订单状态机、管理端维护。"""
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.common.enums import EnableStatus, OrderStatus
from app.common.pagination import PageResult, normalize_page
from app.core.exceptions import ConflictError, NotFoundError, ParamError
from app.core.redis import get_redis
from app.models.mall import Order, OrderItem, Product, ProductCategory
from app.models.user import User
from app.repositories.mall import MallRepository
from app.schemas.mall import (
    CartItemAdd,
    CartItemOut,
    CartItemUpdate,
    CheckoutCreate,
    OrderItemOut,
    OrderOut,
    ProductCategoryCreate,
    ProductCategoryOut,
    ProductCategoryUpdate,
    ProductCreate,
    ProductOut,
    ProductUpdate,
)
from app.utils.order_no import gen_no
from app.utils.time import to_iso, utcnow


def _cart_key(user_id: int) -> str:
    return f"cart:{user_id}"


# ---------------- 公开查询 ----------------

def list_categories(db: Session) -> list[ProductCategoryOut]:
    stmt = (
        select(ProductCategory)
        .where(ProductCategory.status == EnableStatus.ACTIVE.value)
        .order_by(ProductCategory.sort, ProductCategory.id)
    )
    return [ProductCategoryOut.model_validate(r) for r in db.execute(stmt).scalars().all()]


def _product_out(p: Product) -> ProductOut:
    return ProductOut(
        id=p.id,
        category_id=p.category_id,
        category_name=p.category.name if p.category else None,
        name=p.name,
        subtitle=p.subtitle,
        description=p.description,
        cover_image=p.cover_image,
        price=p.price,
        stock=p.stock,
        sales=p.sales,
        status=p.status,
    )


def list_products(
    db: Session,
    page: int,
    page_size: int,
    category_id: int | None = None,
    keyword: str | None = None,
) -> PageResult:
    stmt = select(Product).where(Product.status == EnableStatus.ACTIVE.value)
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(Product.name.like(like), Product.subtitle.like(like)))
    stmt = stmt.order_by(Product.id.desc())

    page, page_size = normalize_page(page, page_size)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.limit(page_size).offset((page - 1) * page_size)).scalars().all()
    return PageResult(
        items=[_product_out(p) for p in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_product(db: Session, product_id: int) -> ProductOut:
    p = MallRepository(db).get_product(product_id)
    if not p or p.status != EnableStatus.ACTIVE.value:
        raise NotFoundError("商品不存在")
    return _product_out(p)


# ---------------- 购物车 ----------------

def _read_cart_items(db: Session, user_id: int) -> list[tuple[Product, int]]:
    """从 Redis 读取购物车并关联商品，仅保留有效在售商品（顺带清理失效项）。"""
    redis = get_redis()
    key = _cart_key(user_id)
    raw = redis.hgetall(key) or {}
    items: list[tuple[Product, int]] = []
    stale: list[str] = []
    for pid_str, qty_str in raw.items():
        try:
            pid = int(pid_str)
            qty = int(qty_str)
        except (TypeError, ValueError):
            stale.append(pid_str)
            continue
        if qty <= 0:
            stale.append(pid_str)
            continue
        product = db.get(Product, pid)
        if not product or product.status != EnableStatus.ACTIVE.value:
            stale.append(pid_str)
            continue
        items.append((product, qty))
    if stale:
        redis.hdel(key, *stale)
    items.sort(key=lambda x: x[0].id)
    return items


def add_to_cart(db: Session, user_id: int, data: CartItemAdd) -> CartItemOut:
    repo = MallRepository(db)
    product = repo.get_product(data.product_id)
    if not product or product.status != EnableStatus.ACTIVE.value:
        raise NotFoundError("商品不存在或已下架")

    redis = get_redis()
    key = _cart_key(user_id)
    current = int(redis.hget(key, str(product.id)) or 0)
    new_qty = current + data.quantity
    if new_qty > product.stock:
        raise ConflictError("超过商品库存")
    redis.hset(key, str(product.id), new_qty)
    return _cart_item_out(product, new_qty)


def list_cart(db: Session, user_id: int) -> list[CartItemOut]:
    items = _read_cart_items(db, user_id)
    return [_cart_item_out(p, qty) for p, qty in items]


def _cart_item_out(product: Product, quantity: int) -> CartItemOut:
    return CartItemOut(
        product_id=product.id,
        name=product.name,
        cover_image=product.cover_image,
        price=product.price,
        stock=product.stock,
        quantity=quantity,
        subtotal=product.price * quantity,
    )


def update_cart_item(db: Session, user_id: int, product_id: int, data: CartItemUpdate) -> list[CartItemOut]:
    repo = MallRepository(db)
    product = repo.get_product(product_id)
    if not product or product.status != EnableStatus.ACTIVE.value:
        raise NotFoundError("商品不存在或已下架")

    redis = get_redis()
    key = _cart_key(user_id)
    if data.quantity == 0:
        redis.hdel(key, str(product_id))
    else:
        if data.quantity > product.stock:
            raise ConflictError("超过商品库存")
        redis.hset(key, str(product_id), data.quantity)
    return list_cart(db, user_id)


def remove_cart_item(db: Session, user_id: int, product_id: int) -> list[CartItemOut]:
    redis = get_redis()
    redis.hdel(_cart_key(user_id), str(product_id))
    return list_cart(db, user_id)


def clear_cart(user_id: int) -> None:
    get_redis().delete(_cart_key(user_id))


# ---------------- 下单 ----------------

def _order_out(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        order_no=order.order_no,
        user_id=order.user_id,
        user_nickname=order.user.nickname if order.user else "",
        status=order.status,
        total_amount=order.total_amount,
        receiver_name=order.receiver_name,
        receiver_phone=order.receiver_phone,
        receiver_address=order.receiver_address,
        remark=order.remark,
        items=[
            OrderItemOut(
                id=it.id,
                product_id=it.product_id,
                product_name=it.product_name_snapshot,
                product_cover=it.product_cover_snapshot,
                unit_price=it.unit_price_snapshot,
                quantity=it.quantity,
                subtotal=it.subtotal,
            )
            for it in order.items
        ],
        paid_at=to_iso(order.paid_at),
        shipped_at=to_iso(order.shipped_at),
        completed_at=to_iso(order.completed_at),
        cancelled_at=to_iso(order.cancelled_at),
        created_at=to_iso(order.created_at),
    )


def checkout(db: Session, user_id: int, data: CheckoutCreate) -> OrderOut:
    """从购物车下单：按商品 id 升序加行锁扣减库存，防超卖，明细做快照。"""
    repo = MallRepository(db)
    cart_items = _read_cart_items(db, user_id)
    if not cart_items:
        raise ParamError("购物车为空")

    order = Order(
        order_no=gen_no("O"),
        user_id=user_id,
        status=OrderStatus.PENDING_PAYMENT.value,
        total_amount=Decimal("0"),
        receiver_name=data.receiver_name,
        receiver_phone=data.receiver_phone,
        receiver_address=data.receiver_address,
        remark=data.remark,
    )
    total = Decimal("0")
    for product, qty in cart_items:
        # 重新加锁读取最新库存（避免购物车读取与下单之间的并发窗口）
        locked = repo.get_product_for_update(product.id)
        if not locked or locked.status != EnableStatus.ACTIVE.value:
            raise ConflictError(f"商品已下架：{product.name}")
        if locked.stock < qty:
            raise ConflictError(f"库存不足：{locked.name}（剩余 {locked.stock}）")
        locked.stock -= qty
        locked.sales += qty
        subtotal = locked.price * qty
        total += subtotal
        order.items.append(
            OrderItem(
                product_id=locked.id,
                product_name_snapshot=locked.name,
                product_cover_snapshot=locked.cover_image,
                unit_price_snapshot=locked.price,
                quantity=qty,
                subtotal=subtotal,
            )
        )

    order.total_amount = total
    db.add(order)
    db.commit()
    clear_cart(user_id)
    db.refresh(order)
    return _order_out(order)


# ---------------- 用户订单 ----------------

def list_my_orders(db: Session, user_id: int) -> list[OrderOut]:
    stmt = select(Order).where(Order.user_id == user_id).order_by(Order.id.desc())
    return [_order_out(o) for o in db.execute(stmt).scalars().all()]


def get_my_order(db: Session, user_id: int, order_id: int) -> OrderOut:
    order = MallRepository(db).get_order(order_id)
    if not order or order.user_id != user_id:
        raise NotFoundError("订单不存在")
    return _order_out(order)


def pay_order(db: Session, user_id: int, order_id: int) -> OrderOut:
    """模拟支付：待支付 → 已支付。真实系统此处应接入支付网关回调。"""
    order = MallRepository(db).get_order_for_update(order_id)
    if not order or order.user_id != user_id:
        raise NotFoundError("订单不存在")
    if order.status != OrderStatus.PENDING_PAYMENT.value:
        raise ConflictError("该订单不可支付")
    order.status = OrderStatus.PAID.value
    order.paid_at = utcnow()
    db.commit()
    return _order_out(order)


def cancel_order(db: Session, user_id: int, order_id: int) -> OrderOut:
    """取消待支付订单并回滚库存与销量。"""
    repo = MallRepository(db)
    order = repo.get_order_for_update(order_id)
    if not order or order.user_id != user_id:
        raise NotFoundError("订单不存在")
    if order.status != OrderStatus.PENDING_PAYMENT.value:
        raise ConflictError("仅待支付订单可取消")
    for item in order.items:
        product = repo.get_product_for_update(item.product_id)
        if product:
            product.stock += item.quantity
            product.sales = max(0, product.sales - item.quantity)
    order.status = OrderStatus.CANCELLED.value
    order.cancelled_at = utcnow()
    db.commit()
    return _order_out(order)


# ---------------- 管理端：订单处理 ----------------

def list_admin_orders(
    db: Session,
    page: int,
    page_size: int,
    status: str | None = None,
    keyword: str | None = None,
) -> PageResult:
    stmt = select(Order)
    if status:
        stmt = stmt.where(Order.status == status)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                Order.order_no.like(like),
                Order.receiver_name.like(like),
                Order.receiver_phone.like(like),
            )
        )
    stmt = stmt.order_by(Order.id.desc())

    page, page_size = normalize_page(page, page_size)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.limit(page_size).offset((page - 1) * page_size)).scalars().all()
    return PageResult(
        items=[_order_out(o) for o in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


def ship_order(db: Session, admin: User, order_id: int) -> OrderOut:
    order = MallRepository(db).get_order_for_update(order_id)
    if not order:
        raise NotFoundError("订单不存在")
    if order.status != OrderStatus.PAID.value:
        raise ConflictError("仅已支付订单可发货")
    order.status = OrderStatus.SHIPPED.value
    order.shipped_at = utcnow()
    db.commit()
    return _order_out(order)


def complete_order(db: Session, admin: User, order_id: int) -> OrderOut:
    order = MallRepository(db).get_order_for_update(order_id)
    if not order:
        raise NotFoundError("订单不存在")
    if order.status != OrderStatus.SHIPPED.value:
        raise ConflictError("仅已发货订单可标记完成")
    order.status = OrderStatus.COMPLETED.value
    order.completed_at = utcnow()
    db.commit()
    return _order_out(order)


# ---------------- 管理端：分类维护 ----------------

def _require_category(db: Session, category_id: int) -> ProductCategory:
    cat = MallRepository(db).get_category(category_id)
    if not cat:
        raise NotFoundError("商品分类不存在")
    return cat


def list_admin_categories(db: Session) -> list[ProductCategoryOut]:
    stmt = select(ProductCategory).order_by(ProductCategory.sort, ProductCategory.id)
    return [ProductCategoryOut.model_validate(r) for r in db.execute(stmt).scalars().all()]


def create_category(db: Session, data: ProductCategoryCreate) -> ProductCategoryOut:
    cat = ProductCategory(
        name=data.name,
        description=data.description,
        sort=data.sort,
        status=data.status.value,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return ProductCategoryOut.model_validate(cat)


def update_category(
    db: Session, category_id: int, data: ProductCategoryUpdate
) -> ProductCategoryOut:
    cat = _require_category(db, category_id)
    payload = data.model_dump(exclude_unset=True)
    if "status" in payload:
        payload["status"] = payload["status"].value
    for k, v in payload.items():
        setattr(cat, k, v)
    db.commit()
    return ProductCategoryOut.model_validate(cat)


def delete_category(db: Session, category_id: int) -> None:
    cat = _require_category(db, category_id)
    if MallRepository(db).count_products_for_category(category_id) > 0:
        raise ConflictError("该分类下存在商品，请先迁移或停用")
    db.delete(cat)
    db.commit()


# ---------------- 管理端：商品维护 ----------------

def _require_product(db: Session, product_id: int) -> Product:
    p = MallRepository(db).get_product(product_id)
    if not p:
        raise NotFoundError("商品不存在")
    return p


def list_admin_products(db: Session, category_id: int | None = None) -> list[ProductOut]:
    stmt = select(Product)
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    stmt = stmt.order_by(Product.id.desc())
    return [_product_out(p) for p in db.execute(stmt).scalars().all()]


def create_product(db: Session, data: ProductCreate) -> ProductOut:
    _require_category(db, data.category_id)
    p = Product(
        category_id=data.category_id,
        name=data.name,
        subtitle=data.subtitle,
        description=data.description,
        cover_image=data.cover_image,
        price=data.price,
        stock=data.stock,
        sales=0,
        status=data.status.value,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _product_out(p)


def update_product(db: Session, product_id: int, data: ProductUpdate) -> ProductOut:
    p = _require_product(db, product_id)
    payload = data.model_dump(exclude_unset=True)
    if "category_id" in payload:
        _require_category(db, payload["category_id"])
    if "status" in payload:
        payload["status"] = payload["status"].value
    for k, v in payload.items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return _product_out(p)


def delete_product(db: Session, product_id: int) -> None:
    p = _require_product(db, product_id)
    if db.scalar(select(OrderItem.id).where(OrderItem.product_id == product_id).limit(1)):
        raise ConflictError("该商品已被订单引用，请停用而非删除")
    db.delete(p)
    db.commit()
