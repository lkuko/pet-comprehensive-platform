"""健康检查、统一响应与请求 ID 中间件的冒烟测试。"""
from fastapi.testclient import TestClient


def test_health(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"code": 0, "message": "success", "data": {"status": "ok"}}


def test_ping(client: TestClient):
    resp = client.get("/api/v1/ping")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"] == {"pong": True}


def test_request_id_header(client: TestClient):
    resp = client.get("/health")
    assert resp.headers.get("X-Request-ID")


def test_health_ready_without_infra(client: TestClient):
    """无 MySQL/Redis 时，就绪探针应优雅返回 503 而非崩溃。"""
    resp = client.get("/health/ready")
    assert resp.status_code == 503
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["db"] is False
    assert body["data"]["redis"] is False
