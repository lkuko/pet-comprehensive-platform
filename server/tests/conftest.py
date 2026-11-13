"""pytest 全局配置：独立测试环境。

Day 1 骨架测试不依赖数据库（仅覆盖健康检查、统一响应与异常），
通过 APP_ENV=test 标识测试环境；环境变量优先级高于 .env 文件。
后续业务测试（Day 2+）将引入独立测试数据库（SQLite 或专用 MySQL）。
"""
import os

os.environ["APP_ENV"] = "test"
os.environ["APP_DEBUG"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c
