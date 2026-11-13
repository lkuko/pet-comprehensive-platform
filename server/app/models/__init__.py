"""ORM 模型注册入口。

Alembic autogenerate 依赖此文件导入所有模型以发现表结构。
每个业务模块在此 import 对应模型文件。
"""
from app.models.base import Base, TimestampMixin  # noqa: F401
from app.models.pet import (  # noqa: F401
    AdoptionPet,
    AdoptionPetImage,
    PetCategory,
    UserPet,
)
from app.models.user import User  # noqa: F401

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "UserPet",
    "PetCategory",
    "AdoptionPet",
    "AdoptionPetImage",
]
