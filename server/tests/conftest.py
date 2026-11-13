"""pytest 全局配置：独立测试环境。

- 业务数据走 SQLite 内存库（通过依赖覆盖 get_db），不触碰开发/生产库。
- MySQL/Redis 指向封闭端口，确保 /health/ready 等组件探针在测试中不连接真实基础设施。
"""
import os
import tempfile

os.environ["APP_ENV"] = "test"
os.environ["APP_DEBUG"] = "false"
os.environ["MYSQL_PORT"] = "39999"  # 封闭端口，测试不连真实 MySQL
os.environ["REDIS_PORT"] = "39998"  # 封闭端口，测试不连真实 Redis

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import app.models  # noqa: E402,F401  # 确保模型注册
from app.core.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.base import Base  # noqa: E402

# 文件型 SQLite，跨线程（TestClient 使用独立线程）稳定，避免内存库连接生命周期问题
_TMP_DIR = tempfile.mkdtemp(prefix="pet_test_")
engine = create_engine(
    f"sqlite:///{os.path.join(_TMP_DIR, 'test.db')}",
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, expire_on_commit=False
)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    Base.metadata.create_all(engine)
    yield


@pytest.fixture(autouse=True)
def _clean_db():
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    yield session
    session.close()
