"""医疗预约测试：公开查询、预约容量事务、取消释放、管理员处理、排班维护。"""
from datetime import date, time, timedelta

from fastapi.testclient import TestClient

from app.common.enums import MedicalAppointmentStatus
from app.core.security import hash_password
from app.models.medical import (
    DoctorSchedule,
    MedicalAppointment,
    MedicalDoctor,
    MedicalLocation,
    MedicalService,
)
from app.models.pet import UserPet
from app.models.user import User

LOGIN_URL = "/api/v1/user/auth/login"
ADMIN_LOGIN_URL = "/api/v1/admin/auth/login"
APP_URL = "/api/v1/user/medical/appointments"
ADMIN_APP_URL = "/api/v1/admin/medical/appointments"
PUBLIC_URL = "/api/v1/public/medical"


def _location(db, name="测试宠物医院") -> MedicalLocation:
    loc = MedicalLocation(name=name, address="测试地址", phone="021-12345678", status="ACTIVE")
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


def _doctor(db, loc) -> MedicalDoctor:
    doc = MedicalDoctor(
        location_id=loc.id, name="张医生", title="主治医师", specialty="内科", status="ACTIVE"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _service(db, name="基础体检") -> MedicalService:
    svc = MedicalService(name=name, reference_price=99, duration_minutes=30, status="ACTIVE")
    db.add(svc)
    db.commit()
    db.refresh(svc)
    return svc


def _schedule(
    db,
    doc,
    day: date | None = None,
    start=time(9, 0),
    end=time(10, 0),
    capacity=1,
) -> DoctorSchedule:
    if day is None:
        day = date.today() + timedelta(days=1)
    s = DoctorSchedule(
        doctor_id=doc.id,
        location_id=doc.location_id,
        schedule_date=day,
        start_time=start,
        end_time=end,
        capacity=capacity,
        booked_count=0,
        status="ACTIVE",
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


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


def _payload(pet_id: int, schedule_id: int, service_id: int) -> dict:
    return {
        "user_pet_id": pet_id,
        "schedule_id": schedule_id,
        "service_id": service_id,
        "symptom_note": "咳嗽三天",
        "contact_phone": "13800000000",
    }


def test_public_lists(client: TestClient, db):
    loc = _location(db)
    _doctor(db, loc)
    _service(db)
    assert client.get(f"{PUBLIC_URL}/locations").json()["data"][0]["name"] == "测试宠物医院"
    assert client.get(f"{PUBLIC_URL}/doctors").json()["data"][0]["name"] == "张医生"
    assert client.get(f"{PUBLIC_URL}/services").json()["data"][0]["name"] == "基础体检"


def test_schedule_available_and_expired_filter(client: TestClient, db):
    loc = _location(db)
    doc = _doctor(db, loc)
    future = _schedule(db, doc, date.today() + timedelta(days=1), capacity=3)
    expired = _schedule(db, doc, date.today() - timedelta(days=1), time(11, 0), time(12, 0), capacity=3)

    data = client.get(f"{PUBLIC_URL}/schedules", params={"doctor_id": doc.id}).json()["data"]
    ids = {s["id"] for s in data}
    assert future.id in ids
    assert expired.id not in ids
    assert data[0]["remaining"] == 3


def test_create_appointment_success(client: TestClient, db):
    loc = _location(db)
    doc = _doctor(db, loc)
    svc = _service(db)
    s = _schedule(db, doc, capacity=2)
    _, pet, headers = _user_with_pet(client, db)

    resp = client.post(APP_URL, json=_payload(pet.id, s.id, svc.id), headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == MedicalAppointmentStatus.PENDING_CONFIRMATION.value
    assert data["appointment_no"].startswith("M")
    assert data["pet_name"] == "旺财"
    assert data["service_name"] == "基础体检"
    assert data["doctor_name"] == "张医生"

    db.refresh(s)
    assert s.booked_count == 1


def test_create_appointment_requires_auth(client: TestClient, db):
    loc = _location(db)
    doc = _doctor(db, loc)
    svc = _service(db)
    s = _schedule(db, doc)
    resp = client.post(APP_URL, json=_payload(1, s.id, svc.id))
    assert resp.status_code == 401


def test_full_schedule_conflict(client: TestClient, db):
    loc = _location(db)
    doc = _doctor(db, loc)
    svc = _service(db)
    s = _schedule(db, doc, capacity=1)
    _, pet_a, headers_a = _user_with_pet(client, db, "alice")
    _, pet_b, headers_b = _user_with_pet(client, db, "bob")

    assert client.post(APP_URL, json=_payload(pet_a.id, s.id, svc.id), headers=headers_a).status_code == 200
    resp = client.post(APP_URL, json=_payload(pet_b.id, s.id, svc.id), headers=headers_b)
    assert resp.status_code == 409


def test_duplicate_appointment_conflict(client: TestClient, db):
    loc = _location(db)
    doc = _doctor(db, loc)
    svc = _service(db)
    s = _schedule(db, doc, capacity=3)
    _, pet, headers = _user_with_pet(client, db)

    assert client.post(APP_URL, json=_payload(pet.id, s.id, svc.id), headers=headers).status_code == 200
    resp = client.post(APP_URL, json=_payload(pet.id, s.id, svc.id), headers=headers)
    assert resp.status_code == 409


def test_expired_schedule_conflict(client: TestClient, db):
    loc = _location(db)
    doc = _doctor(db, loc)
    svc = _service(db)
    s = _schedule(db, doc, date.today() - timedelta(days=1))
    _, pet, headers = _user_with_pet(client, db)
    resp = client.post(APP_URL, json=_payload(pet.id, s.id, svc.id), headers=headers)
    assert resp.status_code == 409


def test_inactive_schedule_conflict(client: TestClient, db):
    loc = _location(db)
    doc = _doctor(db, loc)
    svc = _service(db)
    s = _schedule(db, doc)
    s.status = "INACTIVE"
    db.commit()
    _, pet, headers = _user_with_pet(client, db)
    resp = client.post(APP_URL, json=_payload(pet.id, s.id, svc.id), headers=headers)
    assert resp.status_code == 409


def test_other_users_pet_not_found(client: TestClient, db):
    loc = _location(db)
    doc = _doctor(db, loc)
    svc = _service(db)
    s = _schedule(db, doc)
    _, _, headers_a = _user_with_pet(client, db, "alice")
    _, pet_b, headers_b = _user_with_pet(client, db, "bob")

    # alice 用 bob 的宠物
    resp = client.post(APP_URL, json=_payload(pet_b.id, s.id, svc.id), headers=headers_a)
    assert resp.status_code == 404


def test_cancel_releases_slot(client: TestClient, db):
    loc = _location(db)
    doc = _doctor(db, loc)
    svc = _service(db)
    s = _schedule(db, doc, capacity=2)
    _, pet, headers = _user_with_pet(client, db)

    app_id = client.post(APP_URL, json=_payload(pet.id, s.id, svc.id), headers=headers).json()["data"]["id"]
    db.refresh(s)
    assert s.booked_count == 1

    resp = client.post(f"{APP_URL}/{app_id}/cancel", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == MedicalAppointmentStatus.CANCELLED.value
    db.refresh(s)
    assert s.booked_count == 0

    # 重复取消冲突
    assert client.post(f"{APP_URL}/{app_id}/cancel", headers=headers).status_code == 409


def test_confirm_and_complete_flow(client: TestClient, db):
    loc = _location(db)
    doc = _doctor(db, loc)
    svc = _service(db)
    s = _schedule(db, doc)
    _, pet, headers = _user_with_pet(client, db)
    admin_headers = _admin_headers(client, db)

    app_id = client.post(APP_URL, json=_payload(pet.id, s.id, svc.id), headers=headers).json()["data"]["id"]

    resp = client.post(f"{ADMIN_APP_URL}/{app_id}/confirm", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == MedicalAppointmentStatus.CONFIRMED.value

    # 确认后名额不释放
    db.refresh(s)
    assert s.booked_count == 1

    resp = client.post(f"{ADMIN_APP_URL}/{app_id}/complete", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == MedicalAppointmentStatus.COMPLETED.value


def test_reject_requires_comment_and_releases(client: TestClient, db):
    loc = _location(db)
    doc = _doctor(db, loc)
    svc = _service(db)
    s = _schedule(db, doc)
    _, pet, headers = _user_with_pet(client, db)
    admin_headers = _admin_headers(client, db)

    app_id = client.post(APP_URL, json=_payload(pet.id, s.id, svc.id), headers=headers).json()["data"]["id"]

    assert client.post(f"{ADMIN_APP_URL}/{app_id}/reject", json={}, headers=admin_headers).status_code == 422

    resp = client.post(
        f"{ADMIN_APP_URL}/{app_id}/reject",
        json={"review_comment": "时段已满，建议改约"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == MedicalAppointmentStatus.REJECTED.value
    db.refresh(s)
    assert s.booked_count == 0


def test_confirm_twice_conflict(client: TestClient, db):
    loc = _location(db)
    doc = _doctor(db, loc)
    svc = _service(db)
    s = _schedule(db, doc)
    _, pet, headers = _user_with_pet(client, db)
    admin_headers = _admin_headers(client, db)

    app_id = client.post(APP_URL, json=_payload(pet.id, s.id, svc.id), headers=headers).json()["data"]["id"]
    assert client.post(f"{ADMIN_APP_URL}/{app_id}/confirm", headers=admin_headers).status_code == 200
    assert client.post(f"{ADMIN_APP_URL}/{app_id}/confirm", headers=admin_headers).status_code == 409


def test_admin_list_filters(client: TestClient, db):
    loc = _location(db)
    doc = _doctor(db, loc)
    svc = _service(db)
    s = _schedule(db, doc)
    _, pet, headers = _user_with_pet(client, db)
    admin_headers = _admin_headers(client, db)
    client.post(APP_URL, json=_payload(pet.id, s.id, svc.id), headers=headers)

    data = client.get(ADMIN_APP_URL, params={"status": "PENDING_CONFIRMATION"}, headers=admin_headers).json()["data"]
    assert data["total"] == 1


def test_schedule_overlap_conflict(client: TestClient, db):
    loc = _location(db)
    doc = _doctor(db, loc)
    _schedule(db, doc, start=time(9, 0), end=time(10, 0))
    resp = client.post(
        "/api/v1/admin/medical/schedules",
        json={
            "doctor_id": doc.id, "location_id": loc.id,
            "schedule_date": (date.today() + timedelta(days=1)).isoformat(),
            "start_time": "09:30", "end_time": "10:30", "capacity": 2,
        },
        headers=_admin_headers(client, db),
    )
    assert resp.status_code == 409


def test_delete_schedule_with_unfinished_appointments(client: TestClient, db):
    loc = _location(db)
    doc = _doctor(db, loc)
    svc = _service(db)
    s = _schedule(db, doc)
    _, pet, headers = _user_with_pet(client, db)
    admin_headers = _admin_headers(client, db)
    client.post(APP_URL, json=_payload(pet.id, s.id, svc.id), headers=headers)

    resp = client.delete(f"/api/v1/admin/medical/schedules/{s.id}", headers=admin_headers)
    assert resp.status_code == 409
