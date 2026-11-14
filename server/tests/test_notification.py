"""Day 9 通知与工作台测试：通知 CRUD、业务触发通知、工作台统计、WebSocket 认证。"""
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.common.enums import NotificationBusinessType
from app.core.security import hash_password
from app.models.care import CareAppointment, CareServiceCategory, CareServicePackage
from app.models.mall import Order
from app.models.notification import AdminNotification
from app.models.pet import AdoptionApplication, UserPet
from app.models.user import User
from app.services import dashboard as dashboard_service
from app.services import notification as notif_service

LOGIN_URL = "/api/v1/user/auth/login"
ADMIN_LOGIN_URL = "/api/v1/admin/auth/login"
CARE_URL = "/api/v1/user/care/appointments"
NOTIF_URL = "/api/v1/admin/notifications"
DASH_URL = "/api/v1/admin/dashboard/summary"


def _user_with_token(client: TestClient, db, username="u1") -> tuple[User, str]:
    user = User(
        username=username, password_hash=hash_password("secret123"),
        nickname=username, role="USER", status="ACTIVE",
    )
    db.add(user)
    db.commit()
    token = client.post(LOGIN_URL, json={"username": username, "password": "secret123"}).json()["data"]["token"]
    return user, token


def _admin_with_token(client: TestClient, db, username="boss") -> tuple[User, str]:
    admin = User(
        username=username, password_hash=hash_password("admin123"),
        nickname=username, role="ADMIN", status="ACTIVE",
    )
    db.add(admin)
    db.commit()
    token = client.post(ADMIN_LOGIN_URL, json={"username": username, "password": "admin123"}).json()["data"]["token"]
    return admin, token


def _admin_headers(client: TestClient, db) -> dict:
    _, token = _admin_with_token(client, db)
    return {"Authorization": f"Bearer {token}"}


def _category(db, name="洗浴清洁", service_type="GROOMING") -> CareServiceCategory:
    cat = CareServiceCategory(name=name, service_type=service_type, sort=1, status="ACTIVE")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def _package(db, cat, name="基础洗浴", price="50.00") -> CareServicePackage:
    pkg = CareServicePackage(
        category_id=cat.id, name=name, description="测试套餐",
        price=price, duration_minutes=40, status="ACTIVE",
    )
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg


def _user_with_pet(client: TestClient, db, username="petu"):
    user = User(
        username=username, password_hash=hash_password("secret123"),
        nickname=username, role="USER", status="ACTIVE",
    )
    db.add(user)
    db.commit()
    pet = UserPet(user_id=user.id, name="旺财", category="DOG", gender="MALE", status="ACTIVE")
    db.add(pet)
    db.commit()
    db.refresh(pet)
    token = client.post(LOGIN_URL, json={"username": username, "password": "secret123"}).json()["data"]["token"]
    return user, pet, {"Authorization": f"Bearer {token}"}


def _grooming_payload(pet_id, package_id) -> dict:
    return {
        "user_pet_id": pet_id,
        "package_id": package_id,
        "appointment_time": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "contact_phone": "13800000000",
        "note": "测试",
    }


# ---------------- 通知 service CRUD ----------------

def test_notification_crud(db):
    n = notif_service.create_notification(
        db, NotificationBusinessType.ADOPTION_APPLICATION.value, 1, "收到新的领养申请", "内容"
    )
    db.commit()
    assert notif_service.unread_count(db) == 1

    result = notif_service.list_notifications(db, 1, 10)
    assert result.total == 1
    assert result.items[0].title == "收到新的领养申请"

    notif_service.mark_read(db, n.id)
    assert notif_service.unread_count(db) == 0
    assert notif_service.list_notifications(db, 1, 10, unread_only=True).total == 0


def test_mark_all_read(db):
    for i in range(3):
        db.add(AdminNotification(business_type="X", business_id=i, title=f"t{i}", is_read=False))
    db.commit()
    assert notif_service.unread_count(db) == 3
    assert notif_service.mark_all_read(db) == 3
    assert notif_service.unread_count(db) == 0


def test_mark_business_read(db):
    notif_service.create_notification(db, NotificationBusinessType.PRODUCT_ORDER.value, 99, "收到新的商品订单")
    notif_service.create_notification(db, NotificationBusinessType.ADOPTION_APPLICATION.value, 1, "收到新的领养申请")
    db.commit()
    assert notif_service.unread_count(db) == 2

    # 只标记订单 99 对应的通知，不误伤其他业务
    assert notif_service.mark_business_read(db, NotificationBusinessType.PRODUCT_ORDER.value, 99) == 1
    db.commit()
    assert notif_service.unread_count(db) == 1

    # 不存在的 business_id 不影响
    assert notif_service.mark_business_read(db, NotificationBusinessType.PRODUCT_ORDER.value, 123) == 0
    db.commit()
    assert notif_service.unread_count(db) == 1


# ---------------- 业务触发通知 ----------------

def test_care_booking_creates_notification(client: TestClient, db):
    cat = _category(db)
    pkg = _package(db, cat)
    _, pet, headers = _user_with_pet(client, db)

    resp = client.post(CARE_URL, json=_grooming_payload(pet.id, pkg.id), headers=headers)
    assert resp.status_code == 200

    notifs = notif_service.list_notifications(db, 1, 10)
    assert notifs.total == 1
    n = notifs.items[0]
    assert n.business_type == NotificationBusinessType.SERVICE_BOOKING.value
    assert n.business_id == resp.json()["data"]["id"]
    assert n.is_read is False


# ---------------- 通知 REST API ----------------

def test_notification_api_and_permission(client: TestClient, db):
    _, token = _user_with_token(client, db)
    notif_service.create_notification(db, NotificationBusinessType.PRODUCT_ORDER.value, 1, "收到新的商品订单")
    db.commit()

    # 普通用户访问管理端通知接口应 403
    assert client.get(NOTIF_URL, headers={"Authorization": f"Bearer {token}"}).status_code == 403

    admin_headers = _admin_headers(client, db)
    data = client.get(NOTIF_URL, headers=admin_headers).json()["data"]
    assert data["total"] == 1

    nid = data["items"][0]["id"]
    assert client.get(f"{NOTIF_URL}/unread-count", headers=admin_headers).json()["data"]["count"] == 1

    resp = client.post(f"{NOTIF_URL}/{nid}/read", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["is_read"] is True
    assert client.get(f"{NOTIF_URL}/unread-count", headers=admin_headers).json()["data"]["count"] == 0


# ---------------- 工作台统计 ----------------

def test_dashboard_summary(client: TestClient, db):
    # 2 个普通用户
    _user_with_token(client, db, "alice")
    _user_with_token(client, db, "bob")
    admin_headers = _admin_headers(client, db)

    # 待审核领养申请（SQLite 不强制 FK，直接插入）
    db.add(AdoptionApplication(
        application_no="A001", user_id=1, adoption_pet_id=1,
        contact_name="a", contact_phone="b", living_environment="c",
        application_reason="d", status="PENDING",
    ))
    # 待发货订单
    db.add(Order(
        order_no="O001", user_id=1, status="PAID", total_amount=Decimal("10.00"),
        receiver_name="a", receiver_phone="b", receiver_address="c",
    ))
    # 未读通知
    notif_service.create_notification(db, NotificationBusinessType.ADOPTION_APPLICATION.value, 1, "收到新的领养申请")
    db.commit()

    resp = client.get(DASH_URL, headers=admin_headers)
    assert resp.status_code == 200
    s = resp.json()["data"]
    assert s["user_count"] == 2
    assert s["pending_adoption"] == 1
    assert s["pending_ship"] == 1
    assert s["unread_notifications"] == 1
    assert len(s["recent_business"]) == 1
    assert s["recent_business"][0]["business_type"] == NotificationBusinessType.ADOPTION_APPLICATION.value


def test_dashboard_requires_admin(client: TestClient, db):
    _, token = _user_with_token(client, db)
    assert client.get(DASH_URL, headers={"Authorization": f"Bearer {token}"}).status_code == 403
    assert client.get(DASH_URL).status_code == 401


# ---------------- WebSocket 认证 ----------------

def test_websocket_rejects_non_admin(client: TestClient, db):
    _, token = _user_with_token(client, db)
    with client.websocket_connect("/ws/admin/notifications") as ws:
        ws.send_text(json.dumps({"token": token}))
        # 非管理员：服务端关闭连接（1008 策略违规）
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_text()
        assert exc.value.code == 1008


def test_websocket_admin_receives_event(client: TestClient, db):
    _, token = _admin_with_token(client, db)
    cat = _category(db)
    pkg = _package(db, cat)
    _, pet, headers = _user_with_pet(client, db)

    with client.websocket_connect("/ws/admin/notifications") as ws:
        ws.send_text(json.dumps({"token": token}))
        # 触发业务 → 应收到 NEW_BUSINESS 事件
        client.post(CARE_URL, json=_grooming_payload(pet.id, pkg.id), headers=headers)
        msg = ws.receive_json()
        assert msg["event"] == "NEW_BUSINESS"
        assert msg["business_type"] == NotificationBusinessType.SERVICE_BOOKING.value
        assert msg["title"] == "收到新的洗护/寄养预约"
