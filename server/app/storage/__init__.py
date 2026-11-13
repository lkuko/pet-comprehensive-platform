"""存储模块：统一导出本地存储实例。"""
from app.storage.local import storage  # noqa: F401

__all__ = ["storage"]
