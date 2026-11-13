"""认证与个人资料测试：注册、登录、管理员登录、越权、禁用。"""
import pytest
from fastapi.testclient import TestClient

from app.common.enums import UserRole, UserStatus
from app.core.deps import get_current_admin
from app.core.exceptions import ForbiddenError
from app.core.security import hash_password
from app.models.user import User

REGISTER_URL = "/api/v1/user/auth/register"
LOGIN_URL = "/api/v1/user/auth/login"
ADMIN_LOGIN_URL = "/api/v1/admin/auth/login"
PROFILE_URL = "/api/v1/user/profile"


def _register(client: TestClient, username="alice", password="secret123", **extra):
    return client.post(REGISTER_URL, json={"username": username, "password": password, **extra})


def _login(client: TestClient, username="alice", password="secret123"):
    return client.post(LOGIN_URL, json={"username": username, "password": password})


def _create_user(db, username, password, role=UserRole.USER.value, status=UserStatus.ACTIVE.value):
    user = User(
        username=username,
        password_hash=hash_password(password),
        nickname=username,
        role=role,
        status=status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_register_success_and_no_password_leak(client: TestClient):
    resp = _register(client)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["token"]
    assert data["user"]["username"] == "alice"
    assert data["user"]["role"] == "USER"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]


def test_register_duplicate_username(client: TestClient):
    assert _register(client).status_code == 200
    resp = _register(client)
    assert resp.status_code == 409
    assert resp.json()["code"] == 40900


def test_register_duplicate_phone(client: TestClient):
    assert _register(client, "alice").status_code == 200
    assert _register(client, "bob", phone="13800000000").status_code == 200
    resp = _register(client, "carol", phone="13800000000")
    assert resp.status_code == 409


def test_register_invalid_username(client: TestClient):
    resp = client.post(REGISTER_URL, json={"username": "a", "password": "secret123"})
    assert resp.status_code == 422


def test_login_success_and_wrong_password(client: TestClient):
    _register(client)
    assert _login(client).status_code == 200
    resp = client.post(LOGIN_URL, json={"username": "alice", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["code"] == 40100


def test_admin_login_rejects_normal_user(client: TestClient):
    _register(client)
    resp = client.post(ADMIN_LOGIN_URL, json={"username": "alice", "password": "secret123"})
    assert resp.status_code == 403
    assert resp.json()["code"] == 40300


def test_admin_login_success(client: TestClient, db):
    _create_user(db, "boss", "admin123", role=UserRole.ADMIN.value)
    resp = client.post(ADMIN_LOGIN_URL, json={"username": "boss", "password": "admin123"})
    assert resp.status_code == 200
    assert resp.json()["data"]["user"]["role"] == "ADMIN"


def test_disabled_user_login_forbidden(client: TestClient, db):
    _create_user(db, "alice", "secret123", status=UserStatus.DISABLED.value)
    resp = _login(client)
    assert resp.status_code == 403


def test_profile_requires_auth(client: TestClient):
    assert client.get(PROFILE_URL).status_code == 401


def test_profile_get_and_update(client: TestClient):
    _register(client)
    token = _login(client).json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get(PROFILE_URL, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["username"] == "alice"

    resp2 = client.put(PROFILE_URL, json={"nickname": "爱丽丝"}, headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["data"]["nickname"] == "爱丽丝"


def test_profile_update_phone_conflict(client: TestClient):
    _register(client, "alice")
    _register(client, "bob", phone="13800000000")
    token = _login(client).json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.put(PROFILE_URL, json={"phone": "13800000000"}, headers=headers)
    assert resp.status_code == 409


def test_get_current_admin_dependency():
    normal = User(id=1, username="u", password_hash="h", nickname="u", role=UserRole.USER.value, status="ACTIVE")
    admin = User(id=2, username="a", password_hash="h", nickname="a", role=UserRole.ADMIN.value, status="ACTIVE")
    with pytest.raises(ForbiddenError):
        get_current_admin(user=normal)
    assert get_current_admin(user=admin) is admin
