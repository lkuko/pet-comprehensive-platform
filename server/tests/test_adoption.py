"""领养与上传测试：公开列表/详情、管理员维护、图片上传校验。"""
from fastapi.testclient import TestClient

from app.common.enums import AdoptionPetStatus, UserRole
from app.core.security import hash_password
from app.models.pet import AdoptionPet, PetCategory
from app.models.user import User
from app.utils.time import utcnow

PUBLIC_LIST_URL = "/api/v1/public/adoption-pets"
PUBLIC_CAT_URL = "/api/v1/public/pet-categories"
ADMIN_PETS_URL = "/api/v1/admin/adoption-pets"
ADMIN_LOGIN_URL = "/api/v1/admin/auth/login"
UPLOAD_URL = "/api/v1/upload/image"


def _admin_headers(client: TestClient, db) -> dict:
    admin = User(
        username="boss", password_hash=hash_password("admin123"),
        nickname="boss", role=UserRole.ADMIN.value, status="ACTIVE",
    )
    db.add(admin)
    db.commit()
    token = client.post(ADMIN_LOGIN_URL, json={"username": "boss", "password": "admin123"}).json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def _category(db, name="猫", sort=1) -> PetCategory:
    cat = PetCategory(name=name, sort=sort, status="ACTIVE")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def _available_pet(db, category_id, name="小白") -> AdoptionPet:
    pet = AdoptionPet(
        category_id=category_id, name=name, breed="中华田园猫", gender="MALE",
        age_months=6, weight=2.5, health_status="健康", vaccinated=True,
        neutered=True, region="北京", description="可爱", status="AVAILABLE",
        published_at=utcnow(),
    )
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet


def test_public_categories_and_list(client: TestClient, db):
    cat = _category(db)
    _available_pet(db, cat.id, "小白")
    _available_pet(db, cat.id, "花花")

    cats = client.get(PUBLIC_CAT_URL).json()["data"]
    assert len(cats) == 1 and cats[0]["name"] == "猫"

    listed = client.get(PUBLIC_LIST_URL).json()["data"]
    assert listed["total"] == 2
    assert {p["name"] for p in listed["items"]} == {"小白", "花花"}
    assert listed["items"][0]["category_name"] == "猫"


def test_public_list_filters(client: TestClient, db):
    cat = _category(db)
    dog = _category(db, "狗", 2)
    _available_pet(db, cat.id, "小白")
    _available_pet(db, dog.id, "旺财")

    by_cat = client.get(PUBLIC_LIST_URL, params={"category_id": cat.id}).json()["data"]
    assert by_cat["total"] == 1 and by_cat["items"][0]["name"] == "小白"

    by_kw = client.get(PUBLIC_LIST_URL, params={"keyword": "旺"}).json()["data"]
    assert by_kw["total"] == 1 and by_kw["items"][0]["name"] == "旺财"


def test_public_detail_only_available(client: TestClient, db):
    cat = _category(db)
    pet = _available_pet(db, cat.id, "小白")
    assert client.get(f"{PUBLIC_LIST_URL}/{pet.id}").status_code == 200

    pet.status = "DRAFT"
    db.commit()
    assert client.get(f"{PUBLIC_LIST_URL}/{pet.id}").status_code == 404


def test_admin_create_update_status(client: TestClient, db):
    headers = _admin_headers(client, db)
    cat = _category(db)

    resp = client.post(
        ADMIN_PETS_URL,
        json={
            "category_id": cat.id, "name": "雪球", "breed": "布偶", "gender": "FEMALE",
            "age_months": 9, "weight": 3.0, "health_status": "健康", "vaccinated": True,
            "neutered": True, "personality": "黏人", "adoption_requirements": "室内养",
            "region": "苏州", "description": "蓝眼布偶", "images": ["/uploads/pets/a.jpg", "/uploads/pets/b.jpg"],
            "status": "DRAFT",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    pet_id = data["id"]
    assert data["status"] == "DRAFT"
    assert data["images"] == ["/uploads/pets/a.jpg", "/uploads/pets/b.jpg"]
    assert data["cover_url"] == "/uploads/pets/a.jpg"

    # 上架：published_at 被赋值
    resp = client.patch(f"{ADMIN_PETS_URL}/{pet_id}/status", json={"status": "AVAILABLE"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "AVAILABLE"
    assert data["published_at"] is not None

    # 上架后出现在公开列表
    assert client.get(PUBLIC_LIST_URL, params={"keyword": "雪球"}).json()["data"]["total"] == 1

    # 编辑
    resp = client.put(f"{ADMIN_PETS_URL}/{pet_id}", json={"name": "雪球2", "images": ["/uploads/pets/c.jpg"]}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "雪球2"
    assert resp.json()["data"]["images"] == ["/uploads/pets/c.jpg"]


def test_admin_requires_admin_role(client: TestClient, db):
    # 普通用户访问管理端应 401（无 token）或 403（有 token 但非管理员）
    assert client.get(ADMIN_PETS_URL).status_code == 401
    # 创建管理员后验证权限依赖（通过普通用户 token 访问）
    user = User(username="u", password_hash=hash_password("secret123"), nickname="u",
                role=UserRole.USER.value, status="ACTIVE")
    db.add(user)
    db.commit()
    from app.core.deps import get_current_admin
    from app.core.exceptions import ForbiddenError
    import pytest
    with pytest.raises(ForbiddenError):
        get_current_admin(user=user)


def test_upload_requires_auth_and_validates(client: TestClient, db):
    # 未登录 401
    resp = client.post(UPLOAD_URL, files={"file": ("a.jpg", b"data", "image/jpeg")})
    assert resp.status_code == 401

    headers = _admin_headers(client, db)
    # 非法扩展名
    resp = client.post(UPLOAD_URL, files={"file": ("a.exe", b"data", "application/octet-stream")}, headers=headers)
    assert resp.status_code == 400
    assert resp.json()["code"] == 40001

    # 非法子目录
    resp = client.post(
        UPLOAD_URL,
        files={"file": ("a.jpg", b"data", "image/jpeg")},
        data={"subdir": "../etc"},
        headers=headers,
    )
    assert resp.status_code == 400

    # 合法上传
    resp = client.post(
        UPLOAD_URL,
        files={"file": ("a.jpg", b"\xff\xd8\xff\xe0fakejpeg", "image/jpeg")},
        data={"subdir": "pets"},
        headers=headers,
    )
    assert resp.status_code == 200
    url = resp.json()["data"]["url"]
    assert url.startswith("/uploads/pets/") and url.endswith(".jpg")
