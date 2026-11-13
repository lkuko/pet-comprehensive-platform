"""SQLAlchemy 2.x 引擎与 Session 管理（同步模式）。

约定：V1 统一使用同步 SQLAlchemy + PyMySQL；路由声明普通 def，
避免在 async def 中执行阻塞数据库调用。事务由 Service 层显式提交/回滚。
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.app_debug,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：每个请求独立 Session，请求结束确保关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
