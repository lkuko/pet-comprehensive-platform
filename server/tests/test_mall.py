"""商城测试：公开查询、购物车、下单锁库存、支付/取消回滚、订单状态机、删除保护。

购物车依赖 Redis，测试中以内存 Fake 替换 get_redis（conftest 已把真实 Redis 指向封闭端口）。
"""
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models.mall import Order, Product, ProductCategory
from app.models.user import User
from app.services import mall as mall_service

LOGIN_URL = "/api/v1/user/auth/login"
ADMIN_LOGIN_URL = "/api/v1/admin/auth/login"
PUBLIC_URL = "/api/v1/public/mall"
CART_URL = "/api/v1/user/cart"
ORDER_URL = "/api/v1/user/orders"
ADMIN_URL = "/api/v1/admin/mall"


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
