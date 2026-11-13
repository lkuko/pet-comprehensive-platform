"""FastAPI 依赖统一出口。

Day 1 提供 get_db；get_current_user / get_current_admin 依赖 users 模型，
将在 Day 2 认证模块落地（JWT 校验 + USER/ADMIN 角色）。
"""
from app.core.database import get_db  # noqa: F401

__all__ = ["get_db"]
