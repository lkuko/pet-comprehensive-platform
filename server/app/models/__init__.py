"""ORM 模型注册入口。

Alembic autogenerate 依赖此文件导入所有模型以发现表结构。
每个业务模块在此 import 对应模型文件。
"""
from app.models.base import Base, TimestampMixin  # noqa: F401
from app.models.care import (  # noqa: F401
    CareAppointment,
    CareServiceCategory,
    CareServicePackage,
)
from app.models.mall import (  # noqa: F401
    InventoryLog,
    Order,
    OrderItem,
    Product,
    ProductCategory,
    UserAddress,
)
from app.models.medical import (  # noqa: F401
    DoctorSchedule,
    MedicalAppointment,
    MedicalDoctor,
    MedicalLocation,
    MedicalService,
)
from app.models.notification import AdminNotification  # noqa: F401
from app.models.pet import (  # noqa: F401
    AdoptionApplication,
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
    "AdoptionApplication",
    "MedicalLocation",
    "MedicalDoctor",
    "MedicalService",
    "DoctorSchedule",
    "MedicalAppointment",
    "CareServiceCategory",
    "CareServicePackage",
    "CareAppointment",
    "ProductCategory",
    "Product",
    "Order",
    "OrderItem",
    "UserAddress",
    "InventoryLog",
    "AdminNotification",
]
