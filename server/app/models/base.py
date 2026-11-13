"""ORM 基类与通用 Mixin。

所有业务表继承 Base；需要审计时间字段的表混入 TimestampMixin。
时间统一按 UTC 写入，业务时区语义由应用层负责。
"""
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有 ORM 模型的基类，统一元数据入口（供 Alembic autogenerate 使用）。"""


class TimestampMixin:
    """通用创建/更新时间戳。"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
