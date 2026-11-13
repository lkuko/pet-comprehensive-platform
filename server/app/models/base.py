"""ORM 基类与通用 Mixin。

所有业务表继承 Base；需要审计时间字段的表混入 TimestampMixin。
时间统一按无时区 UTC 写入（由应用层控制，不依赖数据库服务器时区），
业务时区语义由应用层负责。
"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.utils.time import utcnow

# 主键类型：MySQL 使用 BIGINT（见基线文档），SQLite（测试用）降级为 INTEGER 以支持自增
PkType = BigInteger().with_variant(Integer, "sqlite")


class Base(DeclarativeBase):
    """所有 ORM 模型的基类，统一元数据入口（供 Alembic autogenerate 使用）。"""


class TimestampMixin:
    """通用创建/更新时间戳（无时区 UTC）。"""

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )
