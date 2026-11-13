"""领养申请与审核测试：提交、重复、撤回、越权、审核通过/拒绝、状态事务。"""
from fastapi.testclient import TestClient

from app.common.enums import AdoptionPetStatus, UserRole
from app.core.security import hash_password
from app.models.pet import AdoptionPet, PetCategory
from app.models.user import User
from app.utils.time import utcnow

USER_APP_URL = "/api/v1/user/adoption-applications"
ADMIN_APP_URL = "/api/v1/admin/adoption-applications"
USER_LOGIN_URL = "/api/v1/user/auth/login"
ADMIN_LOGIN_URL = "/api/v1/admin/auth/login"


def _user(client: TestClient, db, username="u1") -> tuple[User, dict]:
    user = User(
        username=username, password_hash=hash_password("secret123"),
        nickname=username, role=UserRole.USER.value, status="ACTIVE",
    )
    db.add(user)
    db.commit()
    token = client.post(
        USER_LOGIN_URL, json={"username": username, "password": "secret123"}
    ).json()["data"]["token"]
    return user, {"Authorization": f"Bearer {token}"}


def _admin_headers(client: TestClient, db) -> dict:
    admin = User(
        username="boss", password_hash=hash_password("admin123"),
        nickname="boss", role=UserRole.ADMIN.value, status="ACTIVE",
    )
    db.add(admin)
    db.commit()
    token = client.post(ADMIN_LOGIN_URL, json={"username": "boss", "password": "admin123"}).json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def _pet(db, status="AVAILABLE", name="小白") -> AdoptionPet:
    cat = PetCategory(name="猫", sort=1, status="ACTIVE")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    pet = AdoptionPet(
        category_id=cat.id, name=name, breed="中华田园猫", gender="MALE",
        age_months=6, weight=2.5, health_status="健康", vaccinated=True,
        neutered=True, region="北京", description="可爱", status=status,
        published_at=utcnow() if status == "AVAILABLE" else None,
    )
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet


def _payload(pet_id: int) -> dict:
    return {
        "adoption_pet_id": pet_id,
        "contact_name": "张三",
        "contact_phone": "13800000000",
        "living_environment": "两居室，有阳台",
        "pet_experience": "养过猫三年",
        "application_reason": "想给家里添个新成员",
    }


def test_create_application_success(client: TestClient, db):
    pet = _pet(db)
    _, headers = _user(client, db)
    resp = client.post(USER_APP_URL, json=_payload(pet.id), headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "PENDING"
    assert data["application_no"].startswith("A")
    assert data["pet_name"] == "小白"
    assert data["user_nickname"] == "u1"


def test_create_application_requires_auth(client: TestClient, db):
    pet = _pet(db)
    resp = client.post(USER_APP_URL, json=_payload(pet.id))
    assert resp.status_code == 401


def test_create_application_rejects_non_available(client: TestClient, db):
    pet = _pet(db, status="DRAFT")
    _, headers = _user(client, db)
    resp = client.post(USER_APP_URL, json=_payload(pet.id), headers=headers)
    assert resp.status_code == 409


def test_duplicate_pending_application_conflict(client: TestClient, db):
    pet = _pet(db)
    _, headers = _user(client, db)
    assert client.post(USER_APP_URL, json=_payload(pet.id), headers=headers).status_code == 200
    resp = client.post(USER_APP_URL, json=_payload(pet.id), headers=headers)
    assert resp.status_code == 409


def test_cancel_and_recancel_conflict(client: TestClient, db):
    pet = _pet(db)
    _, headers = _user(client, db)
    app_id = client.post(USER_APP_URL, json=_payload(pet.id), headers=headers).json()["data"]["id"]

    resp = client.post(f"{USER_APP_URL}/{app_id}/cancel", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "CANCELLED"

    resp = client.post(f"{USER_APP_URL}/{app_id}/cancel", headers=headers)
    assert resp.status_code == 409


def test_cannot_access_other_users_application(client: TestClient, db):
    pet = _pet(db)
    _, headers_a = _user(client, db, "alice")
    app_id = client.post(USER_APP_URL, json=_payload(pet.id), headers=headers_a).json()["data"]["id"]

    _, headers_b = _user(client, db, "bob")
    assert client.get(f"{USER_APP_URL}/{app_id}", headers=headers_b).status_code == 404
    assert client.post(f"{USER_APP_URL}/{app_id}/cancel", headers=headers_b).status_code == 404


def test_approve_sets_pet_adopted_and_closes_others(client: TestClient, db):
    pet = _pet(db)
    _, headers_a = _user(client, db, "alice")
    _, headers_b = _user(client, db, "bob")
    app_a = client.post(USER_APP_URL, json=_payload(pet.id), headers=headers_a).json()["data"]
    app_b = client.post(USER_APP_URL, json=_payload(pet.id), headers=headers_b).json()["data"]

    admin_headers = _admin_headers(client, db)
    resp = client.post(f"{ADMIN_APP_URL}/{app_a['id']}/approve", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "APPROVED"

    # 宠物变为 ADOPTED
    db.refresh(pet)
    assert pet.status == AdoptionPetStatus.ADOPTED.value

    # 另一条申请自动关闭
    other = client.get(f"{USER_APP_URL}/{app_b['id']}", headers=headers_b).json()["data"]
    assert other["status"] == "CLOSED"


def test_approve_twice_conflict(client: TestClient, db):
    pet = _pet(db)
    _, headers = _user(client, db)
    app_id = client.post(USER_APP_URL, json=_payload(pet.id), headers=headers).json()["data"]["id"]

    admin_headers = _admin_headers(client, db)
    assert client.post(f"{ADMIN_APP_URL}/{app_id}/approve", headers=admin_headers).status_code == 200
    resp = client.post(f"{ADMIN_APP_URL}/{app_id}/approve", headers=admin_headers)
    assert resp.status_code == 409


def test_reject_requires_comment_and_keeps_pet_available(client: TestClient, db):
    pet = _pet(db)
    _, headers = _user(client, db)
    app_id = client.post(USER_APP_URL, json=_payload(pet.id), headers=headers).json()["data"]["id"]

    admin_headers = _admin_headers(client, db)
    # 空原因被 Pydantic 拦截
    assert client.post(f"{ADMIN_APP_URL}/{app_id}/reject", json={}, headers=admin_headers).status_code == 422

    resp = client.post(
        f"{ADMIN_APP_URL}/{app_id}/reject",
        json={"review_comment": "居住环境不符合要求"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "REJECTED"
    assert resp.json()["data"]["review_comment"] == "居住环境不符合要求"

    # 拒绝后宠物仍可申请
    db.refresh(pet)
    assert pet.status == AdoptionPetStatus.AVAILABLE.value


def test_approve_rejects_offline_pet(client: TestClient, db):
    pet = _pet(db)
    _, headers = _user(client, db)
    app_id = client.post(USER_APP_URL, json=_payload(pet.id), headers=headers).json()["data"]["id"]

    pet.status = AdoptionPetStatus.OFFLINE.value
    db.commit()

    admin_headers = _admin_headers(client, db)
    resp = client.post(f"{ADMIN_APP_URL}/{app_id}/approve", headers=admin_headers)
    assert resp.status_code == 409
