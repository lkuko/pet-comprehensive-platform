"""用户宠物档案测试：增删改查、越权、软删除。"""
from fastapi.testclient import TestClient

PETS_URL = "/api/v1/user/pets"
REGISTER_URL = "/api/v1/user/auth/register"
LOGIN_URL = "/api/v1/user/auth/login"


def _register_login(client: TestClient, username="alice") -> dict:
    client.post(REGISTER_URL, json={"username": username, "password": "secret123"})
    token = client.post(LOGIN_URL, json={"username": username, "password": "secret123"}).json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def _create_pet(client: TestClient, headers: dict, **overrides):
    payload = {"name": "旺财", "category": "DOG", "breed": "金毛", "gender": "MALE", **overrides}
    return client.post(PETS_URL, json=payload, headers=headers)


def test_create_and_list_pet(client: TestClient):
    headers = _register_login(client)
    resp = _create_pet(client, headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "旺财"
    assert data["category"] == "DOG"
    assert data["status"] == "ACTIVE"
    assert data["user_id"] >= 1

    listed = client.get(PETS_URL, headers=headers).json()["data"]
    assert len(listed) == 1
    assert listed[0]["name"] == "旺财"


def test_pet_requires_auth(client: TestClient):
    assert client.get(PETS_URL).status_code == 401
    assert client.post(PETS_URL, json={"name": "x"}).status_code == 401


def test_get_update_delete_pet(client: TestClient):
    headers = _register_login(client)
    pet_id = _create_pet(client, headers).json()["data"]["id"]

    resp = client.get(f"{PETS_URL}/{pet_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "旺财"

    resp = client.put(f"{PETS_URL}/{pet_id}", json={"name": "旺财2", "weight": 12.5}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "旺财2"
    assert resp.json()["data"]["weight"] == 12.5

    assert client.delete(f"{PETS_URL}/{pet_id}", headers=headers).status_code == 200
    # 软删除后列表不再返回
    assert client.get(PETS_URL, headers=headers).json()["data"] == []


def test_cannot_access_others_pet(client: TestClient):
    alice = _register_login(client, "alice")
    bob = _register_login(client, "bob")
    pet_id = _create_pet(client, alice).json()["data"]["id"]

    assert client.get(f"{PETS_URL}/{pet_id}", headers=bob).status_code == 403
    assert client.put(f"{PETS_URL}/{pet_id}", json={"name": "x"}, headers=bob).status_code == 403
    assert client.delete(f"{PETS_URL}/{pet_id}", headers=bob).status_code == 403


def test_pet_not_found(client: TestClient):
    headers = _register_login(client)
    assert client.get(f"{PETS_URL}/99999", headers=headers).status_code == 404
