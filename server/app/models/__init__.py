"""ORM 模型注册入口。

Alembic autogenerate 依赖此文件导入所有模型以发现表结构。
Day 1 骨架暂无业务模型；后续每个模块在此 import 对应模型文件。
"""
from app.models.base import Base, TimestampMixin  # noqa: F401

__all__ = ["Base", "TimestampMixin"]
