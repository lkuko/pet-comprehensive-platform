"""商城测试：公开查询、购物车、下单锁库存、支付/取消回滚、订单状态机、删除保护。

购物车依赖 Redis，测试中以内存 Fake 替换 get_redis（conftest 已把真实 Redis 指向封闭端口）。
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.security import hash_password
from app.models.mall import InventoryLog, Order, Product, ProductCategory
from app.models.user import User
from app.services import mall as mall_service
from app.utils.time import utcnow

LOGIN_URL = "/api/v1/user/auth/login"
ADMIN_LOGIN_URL = "/api/v1/admin/auth/login"
PUBLIC_URL = "/api/v1/public/mall"
CART_URL = "/api/v1/user/cart"
ORDER_URL = "/api/v1/user/orders"
ADMIN_URL = "/api/v1/admin/mall"
ADDRESS_URL = "/api/v1/user/addresses"


class FakeRedis:
    """内存版 Redis，仅实现商城购物车用到的 hash 接口。"""

    def __init__(self):
        self.data: dict[str, dict] = {}

    def hget(self, key, field):
        return self.data.get(key, {}).get(field)

    def hset(self, key, field, value):
        self.data.setdefault(key, {})[field] = str(value)

    def hdel(self, key, *fields):
        d = self.data.get(key, {})
        for f in fields:
            d.pop(f, None)

    def hgetall(self, key):
        return dict(self.data.get(key, {}))

    def delete(self, key):
        self.data.pop(key, None)


@pytest.fixture()
def fake_redis(monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(mall_service, "get_redis", lambda: r)
    return r


def _category(db, name="猫粮") -> ProductCategory:
    cat = ProductCategory(name=name, sort=1, status="ACTIVE")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def _product(db, cat, name="全价成猫粮", price="88.00", stock=100) -> Product:
    p = Product(
        category_id=cat.id, name=name, subtitle="测试商品",
        description="desc", price=price, stock=stock, sales=0, status="ACTIVE",
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _user_headers(client: TestClient, db, username="u1") -> dict:
    user = User(
        username=username, password_hash=hash_password("secret123"),
        nickname=username, role="USER", status="ACTIVE",
    )
    db.add(user)
    db.commit()
    token = client.post(
        LOGIN_URL, json={"username": username, "password": "secret123"}
    ).json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def _admin_headers(client: TestClient, db) -> dict:
    admin = User(
        username="boss", password_hash=hash_password("admin123"),
        nickname="boss", role="ADMIN", status="ACTIVE",
    )
    db.add(admin)
    db.commit()
    token = client.post(
        ADMIN_LOGIN_URL, json={"username": "boss", "password": "admin123"}
    ).json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def _checkout_payload() -> dict:
    return {
        "receiver_name": "张三",
        "receiver_phone": "13800000000",
        "receiver_address": "上海市浦东新区测试路 1 号",
    }


def _dec(v) -> Decimal:
    return Decimal(str(v))


# ---------------- 公开查询 ----------------

def test_public_lists(client: TestClient, db):
    cat = _category(db)
    _product(db, cat)
    assert client.get(f"{PUBLIC_URL}/categories").json()["data"][0]["name"] == "猫粮"

    data = client.get(f"{PUBLIC_URL}/products", params={"category_id": cat.id}).json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["name"] == "全价成猫粮"
    assert data["items"][0]["category_name"] == "猫粮"


# ---------------- 购物车 ----------------

def test_add_and_list_cart(client: TestClient, db, fake_redis):
    cat = _category(db)
    p = _product(db, cat)
    headers = _user_headers(client, db)

    resp = client.post(CART_URL, json={"product_id": p.id, "quantity": 2}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["quantity"] == 2

    data = client.get(CART_URL, headers=headers).json()["data"]
    assert len(data) == 1
    assert data[0]["product_id"] == p.id
    assert _dec(data[0]["subtotal"]) == Decimal("176.00")


def test_cart_exceeds_stock(client: TestClient, db, fake_redis):
    cat = _category(db)
    p = _product(db, cat, stock=3)
    headers = _user_headers(client, db)

    assert client.post(CART_URL, json={"product_id": p.id, "quantity": 4}, headers=headers).status_code == 409


def test_cart_requires_auth(client: TestClient, db, fake_redis):
    assert client.get(CART_URL).status_code == 401


# ---------------- 下单 ----------------

def test_checkout_success(client: TestClient, db, fake_redis):
    cat = _category(db)
    p = _product(db, cat, price="88.00", stock=10)
    headers = _user_headers(client, db)
    client.post(CART_URL, json={"product_id": p.id, "quantity": 3}, headers=headers)

    resp = client.post(ORDER_URL, json=_checkout_payload(), headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["order_no"].startswith("O")
    assert data["status"] == "PENDING_PAYMENT"
    assert _dec(data["total_amount"]) == Decimal("264.00")
    assert len(data["items"]) == 1
    assert data["items"][0]["product_name"] == "全价成猫粮"
    assert _dec(data["items"][0]["unit_price"]) == Decimal("88.00")

    # 库存扣减 + 销量增加 + 购物车清空
    db.expire_all()
    assert db.get(Product, p.id).stock == 7
    assert db.get(Product, p.id).sales == 3
    assert client.get(CART_URL, headers=headers).json()["data"] == []


def test_checkout_empty_cart(client: TestClient, db, fake_redis):
    headers = _user_headers(client, db)
    assert client.post(ORDER_URL, json=_checkout_payload(), headers=headers).status_code == 400


def test_checkout_insufficient_stock(client: TestClient, db, fake_redis):
    cat = _category(db)
    p = _product(db, cat, stock=2)
    headers = _user_headers(client, db)
    client.post(CART_URL, json={"product_id": p.id, "quantity": 2}, headers=headers)
    # 模拟并发：下单前库存被他人扣减
    p.stock = 1
    db.commit()

    resp = client.post(ORDER_URL, json=_checkout_payload(), headers=headers)
    assert resp.status_code == 409
    assert "库存不足" in resp.json()["message"]


# ---------------- 支付 / 取消 / 状态机 ----------------

def test_pay_order(client: TestClient, db, fake_redis):
    cat = _category(db)
    p = _product(db, cat)
    headers = _user_headers(client, db)
    client.post(CART_URL, json={"product_id": p.id, "quantity": 1}, headers=headers)
    order_id = client.post(ORDER_URL, json=_checkout_payload(), headers=headers).json()["data"]["id"]

    resp = client.post(f"{ORDER_URL}/{order_id}/pay", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "PAID"
    assert resp.json()["data"]["paid_at"] is not None
    # 已支付不可再支付
    assert client.post(f"{ORDER_URL}/{order_id}/pay", headers=headers).status_code == 409


def test_cancel_rolls_back_stock(client: TestClient, db, fake_redis):
    cat = _category(db)
    p = _product(db, cat, stock=5)
    headers = _user_headers(client, db)
    client.post(CART_URL, json={"product_id": p.id, "quantity": 3}, headers=headers)
    order_id = client.post(ORDER_URL, json=_checkout_payload(), headers=headers).json()["data"]["id"]

    db.expire_all()
    assert db.get(Product, p.id).stock == 2

    resp = client.post(f"{ORDER_URL}/{order_id}/cancel", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "CANCELLED"

    db.expire_all()
    assert db.get(Product, p.id).stock == 5
    assert db.get(Product, p.id).sales == 0
    # 已取消不可再取消
    assert client.post(f"{ORDER_URL}/{order_id}/cancel", headers=headers).status_code == 409


def test_paid_order_cannot_cancel(client: TestClient, db, fake_redis):
    cat = _category(db)
    p = _product(db, cat)
    headers = _user_headers(client, db)
    client.post(CART_URL, json={"product_id": p.id, "quantity": 1}, headers=headers)
    order_id = client.post(ORDER_URL, json=_checkout_payload(), headers=headers).json()["data"]["id"]
    client.post(f"{ORDER_URL}/{order_id}/pay", headers=headers)
    assert client.post(f"{ORDER_URL}/{order_id}/cancel", headers=headers).status_code == 409


def test_admin_ship_complete(client: TestClient, db, fake_redis):
    cat = _category(db)
    p = _product(db, cat)
    headers = _user_headers(client, db)
    admin_headers = _admin_headers(client, db)
    client.post(CART_URL, json={"product_id": p.id, "quantity": 1}, headers=headers)
    order_id = client.post(ORDER_URL, json=_checkout_payload(), headers=headers).json()["data"]["id"]
    client.post(f"{ORDER_URL}/{order_id}/pay", headers=headers)

    resp = client.post(f"{ADMIN_URL}/orders/{order_id}/ship", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "SHIPPED"

    resp = client.post(f"{ADMIN_URL}/orders/{order_id}/complete", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "COMPLETED"


def test_ship_requires_paid(client: TestClient, db, fake_redis):
    cat = _category(db)
    p = _product(db, cat)
    headers = _user_headers(client, db)
    admin_headers = _admin_headers(client, db)
    client.post(CART_URL, json={"product_id": p.id, "quantity": 1}, headers=headers)
    order_id = client.post(ORDER_URL, json=_checkout_payload(), headers=headers).json()["data"]["id"]

    assert client.post(f"{ADMIN_URL}/orders/{order_id}/ship", headers=admin_headers).status_code == 409


def test_admin_list_orders(client: TestClient, db, fake_redis):
    cat = _category(db)
    p = _product(db, cat)
    headers = _user_headers(client, db)
    admin_headers = _admin_headers(client, db)
    client.post(CART_URL, json={"product_id": p.id, "quantity": 1}, headers=headers)
    client.post(ORDER_URL, json=_checkout_payload(), headers=headers)

    data = client.get(f"{ADMIN_URL}/orders", params={"status": "PENDING_PAYMENT"}, headers=admin_headers).json()["data"]
    assert data["total"] == 1


# ---------------- 删除保护 ----------------

def test_delete_category_with_products_conflict(client: TestClient, db, fake_redis):
    cat = _category(db)
    _product(db, cat)
    admin_headers = _admin_headers(client, db)
    assert client.delete(f"{ADMIN_URL}/categories/{cat.id}", headers=admin_headers).status_code == 409


def test_delete_product_with_order_conflict(client: TestClient, db, fake_redis):
    cat = _category(db)
    p = _product(db, cat)
    headers = _user_headers(client, db)
    admin_headers = _admin_headers(client, db)
    client.post(CART_URL, json={"product_id": p.id, "quantity": 1}, headers=headers)
    client.post(ORDER_URL, json=_checkout_payload(), headers=headers)

    assert client.delete(f"{ADMIN_URL}/products/{p.id}", headers=admin_headers).status_code == 409


def test_admin_crud_category_and_product(client: TestClient, db, fake_redis):
    admin_headers = _admin_headers(client, db)
    cat = client.post(ADMIN_URL + "/categories", json={"name": "玩具"}, headers=admin_headers).json()["data"]
    assert cat["name"] == "玩具"

    p = client.post(
        ADMIN_URL + "/products",
        json={"category_id": cat["id"], "name": "逗猫棒", "price": "25.00", "stock": 100},
        headers=admin_headers,
    ).json()["data"]
    assert p["name"] == "逗猫棒"

    updated = client.put(
        ADMIN_URL + f"/products/{p['id']}", json={"stock": 50}, headers=admin_headers
    ).json()["data"]
    assert updated["stock"] == 50


# ---------------- 收货地址 ----------------

def _address_payload(**kw) -> dict:
    data = {
        "receiver_name": "张三",
        "receiver_phone": "13800000000",
        "province": "上海市",
        "city": "上海市",
        "district": "浦东新区",
        "detail_address": "测试路 1 号",
    }
    data.update(kw)
    return data


def test_address_crud_and_default(client: TestClient, db, fake_redis):
    headers = _user_headers(client, db)
    # 第一条自动设为默认
    a1 = client.post(ADDRESS_URL, json=_address_payload(), headers=headers).json()["data"]
    assert a1["is_default"] is True

    # 第二条显式设默认，第一条被取消默认
    a2 = client.post(ADDRESS_URL, json=_address_payload(is_default=True), headers=headers).json()["data"]
    assert a2["is_default"] is True
    lst = client.get(ADDRESS_URL, headers=headers).json()["data"]
    assert lst[0]["id"] == a2["id"]
    assert lst[1]["id"] == a1["id"]
    assert lst[1]["is_default"] is False

    # 更新
    upd = client.put(
        f"{ADDRESS_URL}/{a1['id']}", json={"detail_address": "新地址 9 号"}, headers=headers
    ).json()["data"]
    assert upd["detail_address"] == "新地址 9 号"

    # 切换默认
    client.post(f"{ADDRESS_URL}/{a1['id']}/default", headers=headers)
    lst = client.get(ADDRESS_URL, headers=headers).json()["data"]
    assert lst[0]["id"] == a1["id"]
    assert lst[0]["is_default"] is True

    # 删除
    client.delete(f"{ADDRESS_URL}/{a2['id']}", headers=headers)
    assert len(client.get(ADDRESS_URL, headers=headers).json()["data"]) == 1


def test_address_isolation(client: TestClient, db, fake_redis):
    h1 = _user_headers(client, db, username="ua")
    h2 = _user_headers(client, db, username="ub")
    client.post(ADDRESS_URL, json=_address_payload(), headers=h1)
    assert client.get(ADDRESS_URL, headers=h2).json()["data"] == []


# ---------------- 下单幂等键 ----------------

def test_checkout_idempotency(client: TestClient, db, fake_redis):
    cat = _category(db)
    p = _product(db, cat, stock=10)
    headers = _user_headers(client, db)
    client.post(CART_URL, json={"product_id": p.id, "quantity": 2}, headers=headers)

    payload = _checkout_payload()
    payload["idempotency_key"] = "idem-001"
    r1 = client.post(ORDER_URL, json=payload, headers=headers).json()["data"]

    # 购物车已清空，但幂等键命中应返回同一订单，不因购物车空而报错
    r2 = client.post(ORDER_URL, json=payload, headers=headers).json()["data"]
    assert r2["id"] == r1["id"]
    assert r2["order_no"] == r1["order_no"]

    # 库存只扣一次
    db.expire_all()
    assert db.get(Product, p.id).stock == 8


# ---------------- 库存流水 ----------------

def _inventory_logs(db, product_id: int) -> list[InventoryLog]:
    return db.execute(
        select(InventoryLog).where(InventoryLog.product_id == product_id).order_by(InventoryLog.id)
    ).scalars().all()


def test_checkout_writes_deduct_log(client: TestClient, db, fake_redis):
    cat = _category(db)
    p = _product(db, cat, stock=10)
    headers = _user_headers(client, db)
    client.post(CART_URL, json={"product_id": p.id, "quantity": 3}, headers=headers)
    client.post(ORDER_URL, json=_checkout_payload(), headers=headers)

    db.expire_all()
    logs = _inventory_logs(db, p.id)
    assert len(logs) == 1
    assert logs[0].change_type == "ORDER_DEDUCT"
    assert logs[0].change_quantity == -3
    assert logs[0].before_stock == 10
    assert logs[0].after_stock == 7


def test_cancel_writes_release_log(client: TestClient, db, fake_redis):
    cat = _category(db)
    p = _product(db, cat, stock=5)
    headers = _user_headers(client, db)
    client.post(CART_URL, json={"product_id": p.id, "quantity": 3}, headers=headers)
    order_id = client.post(ORDER_URL, json=_checkout_payload(), headers=headers).json()["data"]["id"]
    client.post(f"{ORDER_URL}/{order_id}/cancel", headers=headers)

    db.expire_all()
    logs = _inventory_logs(db, p.id)
    assert len(logs) == 2
    assert logs[1].change_type == "ORDER_RELEASE"
    assert logs[1].change_quantity == 3
    assert logs[1].after_stock == 5


def test_admin_adjust_stock_writes_log(client: TestClient, db, fake_redis):
    admin_headers = _admin_headers(client, db)
    cat = _category(db)
    p = _product(db, cat, stock=100)
    client.put(f"{ADMIN_URL}/products/{p.id}", json={"stock": 150}, headers=admin_headers)

    db.expire_all()
    logs = _inventory_logs(db, p.id)
    assert len(logs) == 1
    assert logs[0].change_type == "ADMIN_ADJUST"
    assert logs[0].change_quantity == 50
    assert logs[0].before_stock == 100
    assert logs[0].after_stock == 150


# ---------------- 超时自动关单 ----------------

def test_close_expired_orders(client: TestClient, db, fake_redis):
    cat = _category(db)
    p = _product(db, cat, stock=10)
    headers = _user_headers(client, db)
    client.post(CART_URL, json={"product_id": p.id, "quantity": 4}, headers=headers)
    order_id = client.post(ORDER_URL, json=_checkout_payload(), headers=headers).json()["data"]["id"]

    # 模拟时间流逝 31 分钟，触发超时关单
    closed = mall_service.close_expired_orders(db, now=utcnow() + timedelta(minutes=31))
    assert closed == 1

    db.expire_all()
    assert db.get(Order, order_id).status == "CLOSED"
    assert db.get(Product, p.id).stock == 10  # 库存返还
    logs = _inventory_logs(db, p.id)
    assert logs[-1].change_type == "ORDER_RELEASE"
    assert logs[-1].change_quantity == 4

    # 幂等：再次执行不重复关闭、不重复返还
    assert mall_service.close_expired_orders(db, now=utcnow() + timedelta(minutes=31)) == 0


def test_close_expired_skips_paid(client: TestClient, db, fake_redis):
    cat = _category(db)
    p = _product(db, cat)
    headers = _user_headers(client, db)
    client.post(CART_URL, json={"product_id": p.id, "quantity": 1}, headers=headers)
    order_id = client.post(ORDER_URL, json=_checkout_payload(), headers=headers).json()["data"]["id"]
    client.post(f"{ORDER_URL}/{order_id}/pay", headers=headers)

    assert mall_service.close_expired_orders(db, now=utcnow() + timedelta(minutes=31)) == 0
    db.expire_all()
    assert db.get(Order, order_id).status == "PAID"


# ---------------- 用户确认收货 ----------------

def test_confirm_receipt(client: TestClient, db, fake_redis):
    cat = _category(db)
    p = _product(db, cat)
    headers = _user_headers(client, db)
    admin_headers = _admin_headers(client, db)
    client.post(CART_URL, json={"product_id": p.id, "quantity": 1}, headers=headers)
    order_id = client.post(ORDER_URL, json=_checkout_payload(), headers=headers).json()["data"]["id"]
    client.post(f"{ORDER_URL}/{order_id}/pay", headers=headers)
    client.post(f"{ADMIN_URL}/orders/{order_id}/ship", headers=admin_headers)

    resp = client.post(f"{ORDER_URL}/{order_id}/confirm-receipt", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "COMPLETED"
    assert resp.json()["data"]["completed_at"] is not None


def test_confirm_receipt_requires_shipped(client: TestClient, db, fake_redis):
    cat = _category(db)
    p = _product(db, cat)
    headers = _user_headers(client, db)
    client.post(CART_URL, json={"product_id": p.id, "quantity": 1}, headers=headers)
    order_id = client.post(ORDER_URL, json=_checkout_payload(), headers=headers).json()["data"]["id"]

    assert client.post(f"{ORDER_URL}/{order_id}/confirm-receipt", headers=headers).status_code == 409
