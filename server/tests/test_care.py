"""洗护/寄养测试：公开查询、洗护预约、寄养日期校验、价格快照、取消、管理端处理、删除保护。"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from app.common.enums import CareAppointmentStatus
from app.core.security import hash_password
from app.models.care import CareAppointment, CareServiceCategory, CareServicePackage
from app.models.pet import UserPet
from app.models.user import User

LOGIN_URL = "/api/v1/user/auth/login"
ADMIN_LOGIN_URL = "/api/v1/admin/auth/login"
APP_URL = "/api/v1/user/care/appointments"
ADMIN_APP_URL = "/api/v1/admin/care/appointments"
PUBLIC_URL = "/api/v1/public/care"


def _category(db, name="洗浴清洁", service_type="GROOMING") -> CareServiceCategory:
    cat = CareServiceCategory(name=name, service_type=service_type, sort=1, status="ACTIVE")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def _package(
    db, cat, name="基础洗浴", price="50.00", duration=40
) -> CareServicePackage:
    pkg = CareServicePackage(
        category_id=cat.id, name=name, description="测试套餐",
        price=price, duration_minutes=duration, status="ACTIVE",
    )
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg


def _user_with_pet(client: TestClient, db, username="u1"):
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
    token = client.post(
        LOGIN_URL, json={"username": username, "password": "secret123"}
    ).json()["data"]["token"]
    return user, pet, {"Authorization": f"Bearer {token}"}


def _admin_headers(client: TestClient, db) -> dict:
    admin = User(
        username="boss", password_hash=hash_password("admin123"),
        nickname="boss", role="ADMIN", status="ACTIVE",
    )
    db.add(admin)
    db.commit()
    token = client.post(ADMIN_LOGIN_URL, json={"username": "boss", "password": "admin123"}).json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def _future_dt(days=2) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _grooming_payload(pet_id, package_id, appointment_time=None) -> dict:
    return {
        "user_pet_id": pet_id,
        "package_id": package_id,
        "appointment_time": appointment_time or _future_dt(),
        "contact_phone": "13800000000",
        "note": "请用宠物专用香波",
    }


def _boarding_payload(pet_id, package_id, check_in=None, check_out=None) -> dict:
    if check_in is None:
        check_in = (date.today() + timedelta(days=1)).isoformat()
    if check_out is None:
        check_out = (date.today() + timedelta(days=4)).isoformat()
    return {
        "user_pet_id": pet_id,
        "package_id": package_id,
        "check_in_date": check_in,
        "check_out_date": check_out,
        "contact_phone": "13800000000",
        "note": "自带狗粮",
    }


def _dec(v) -> Decimal:
    return Decimal(str(v))


def test_public_lists(client: TestClient, db):
    cat = _category(db)
    _package(db, cat)
    assert client.get(f"{PUBLIC_URL}/categories").json()["data"][0]["name"] == "洗浴清洁"
    assert client.get(f"{PUBLIC_URL}/packages", params={"category_id": cat.id}).json()["data"][0]["name"] == "基础洗浴"
    # 按类型筛选
    boarding = _category(db, "寄养", "BOARDING")
    data = client.get(f"{PUBLIC_URL}/categories", params={"service_type": "BOARDING"}).json()["data"]
    assert [c["id"] for c in data] == [boarding.id]


def test_grooming_appointment_success(client: TestClient, db):
    cat = _category(db)
    pkg = _package(db, cat, price="50.00")
    _, pet, headers = _user_with_pet(client, db)

    resp = client.post(APP_URL, json=_grooming_payload(pet.id, pkg.id), headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == CareAppointmentStatus.PENDING_CONFIRMATION.value
    assert data["appointment_no"].startswith("C")
    assert data["pet_name"] == "旺财"
    assert data["category_name"] == "洗浴清洁"
    assert data["package_name"] == "基础洗浴"
    assert data["service_type"] == "GROOMING"
    assert _dec(data["price_snapshot"]) == Decimal("50.00")
    assert _dec(data["total_price"]) == Decimal("50.00")
    assert data["appointment_time"] is not None
    assert data["check_in_date"] is None


def test_grooming_past_time_rejected(client: TestClient, db):
    cat = _category(db)
    pkg = _package(db, cat)
    _, pet, headers = _user_with_pet(client, db)

    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    resp = client.post(APP_URL, json=_grooming_payload(pet.id, pkg.id, past), headers=headers)
    assert resp.status_code == 400


def test_grooming_missing_time_rejected(client: TestClient, db):
    cat = _category(db)
    pkg = _package(db, cat)
    _, pet, headers = _user_with_pet(client, db)

    resp = client.post(
        APP_URL,
        json={"user_pet_id": pet.id, "package_id": pkg.id, "contact_phone": "13800000000"},
        headers=headers,
    )
    # 既无预约时间也无寄养日期，schema 拒绝
    assert resp.status_code == 422


def test_boarding_appointment_success(client: TestClient, db):
    cat = _category(db, "寄养", "BOARDING")
    pkg = _package(db, cat, name="标准寄养", price="60.00", duration=0)
    _, pet, headers = _user_with_pet(client, db)

    resp = client.post(APP_URL, json=_boarding_payload(pet.id, pkg.id), headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["service_type"] == "BOARDING"
    # 3 天：60 * 3 = 180
    assert _dec(data["price_snapshot"]) == Decimal("60.00")
    assert _dec(data["total_price"]) == Decimal("180.00")
    assert data["appointment_time"] is None
    assert data["check_in_date"] is not None
    assert data["check_out_date"] is not None


def test_boarding_checkout_not_after_checkin(client: TestClient, db):
    cat = _category(db, "寄养", "BOARDING")
    pkg = _package(db, cat, duration=0)
    _, pet, headers = _user_with_pet(client, db)

    resp = client.post(
        APP_URL,
        json=_boarding_payload(
            pet.id, pkg.id,
            check_in=(date.today() + timedelta(days=2)).isoformat(),
            check_out=(date.today() + timedelta(days=2)).isoformat(),
        ),
        headers=headers,
    )
    assert resp.status_code == 400


def test_boarding_past_checkin_rejected(client: TestClient, db):
    cat = _category(db, "寄养", "BOARDING")
    pkg = _package(db, cat, duration=0)
    _, pet, headers = _user_with_pet(client, db)

    resp = client.post(
        APP_URL,
        json=_boarding_payload(
            pet.id, pkg.id,
            check_in=(date.today() - timedelta(days=1)).isoformat(),
            check_out=(date.today() + timedelta(days=3)).isoformat(),
        ),
        headers=headers,
    )
    assert resp.status_code == 400


def test_mixed_fields_rejected(client: TestClient, db):
    cat = _category(db)
    pkg = _package(db, cat)
    _, pet, headers = _user_with_pet(client, db)

    payload = _grooming_payload(pet.id, pkg.id)
    payload["check_in_date"] = (date.today() + timedelta(days=1)).isoformat()
    resp = client.post(APP_URL, json=payload, headers=headers)
    assert resp.status_code == 422


def test_requires_auth(client: TestClient, db):
    cat = _category(db)
    pkg = _package(db, cat)
    resp = client.post(APP_URL, json=_grooming_payload(1, pkg.id))
    assert resp.status_code == 401


def test_other_users_pet_not_found(client: TestClient, db):
    cat = _category(db)
    pkg = _package(db, cat)
    _, _, headers_a = _user_with_pet(client, db, "alice")
    _, pet_b, _ = _user_with_pet(client, db, "bob")

    resp = client.post(APP_URL, json=_grooming_payload(pet_b.id, pkg.id), headers=headers_a)
    assert resp.status_code == 404


def test_cancel_appointment(client: TestClient, db):
    cat = _category(db)
    pkg = _package(db, cat)
    _, pet, headers = _user_with_pet(client, db)

    app_id = client.post(APP_URL, json=_grooming_payload(pet.id, pkg.id), headers=headers).json()["data"]["id"]
    resp = client.post(f"{APP_URL}/{app_id}/cancel", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == CareAppointmentStatus.CANCELLED.value
    assert client.post(f"{APP_URL}/{app_id}/cancel", headers=headers).status_code == 409


def test_confirm_and_complete_flow(client: TestClient, db):
    cat = _category(db)
    pkg = _package(db, cat)
    _, pet, headers = _user_with_pet(client, db)
    admin_headers = _admin_headers(client, db)

    app_id = client.post(APP_URL, json=_grooming_payload(pet.id, pkg.id), headers=headers).json()["data"]["id"]

    resp = client.post(f"{ADMIN_APP_URL}/{app_id}/confirm", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == CareAppointmentStatus.CONFIRMED.value

    resp = client.post(f"{ADMIN_APP_URL}/{app_id}/complete", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == CareAppointmentStatus.COMPLETED.value


def test_reject_requires_comment(client: TestClient, db):
    cat = _category(db)
    pkg = _package(db, cat)
    _, pet, headers = _user_with_pet(client, db)
    admin_headers = _admin_headers(client, db)

    app_id = client.post(APP_URL, json=_grooming_payload(pet.id, pkg.id), headers=headers).json()["data"]["id"]

    assert client.post(f"{ADMIN_APP_URL}/{app_id}/reject", json={}, headers=admin_headers).status_code == 422

    resp = client.post(
        f"{ADMIN_APP_URL}/{app_id}/reject",
        json={"review_comment": "时段安排冲突"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == CareAppointmentStatus.REJECTED.value


def test_admin_list_filters(client: TestClient, db):
    cat = _category(db)
    pkg = _package(db, cat)
    _, pet, headers = _user_with_pet(client, db)
    admin_headers = _admin_headers(client, db)
    client.post(APP_URL, json=_grooming_payload(pet.id, pkg.id), headers=headers)

    data = client.get(ADMIN_APP_URL, params={"service_type": "GROOMING"}, headers=admin_headers).json()["data"]
    assert data["total"] == 1


def test_delete_category_with_packages_conflict(client: TestClient, db):
    cat = _category(db)
    _package(db, cat)
    admin_headers = _admin_headers(client, db)
    resp = client.delete(f"/api/v1/admin/care/categories/{cat.id}", headers=admin_headers)
    assert resp.status_code == 409


def test_delete_package_with_appointments_conflict(client: TestClient, db):
    cat = _category(db)
    pkg = _package(db, cat)
    _, pet, headers = _user_with_pet(client, db)
    admin_headers = _admin_headers(client, db)
    client.post(APP_URL, json=_grooming_payload(pet.id, pkg.id), headers=headers)

    resp = client.delete(f"/api/v1/admin/care/packages/{pkg.id}", headers=admin_headers)
    assert resp.status_code == 409
