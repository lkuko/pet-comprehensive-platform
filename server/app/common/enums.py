"""业务状态枚举集中定义处。

约定：状态字段使用字符串枚举，避免前后端对数字状态含义不一致。
后续模块在此扩展（如 PetStatus、OrderStatus、AppointmentStatus）。
"""
from enum import StrEnum


class UserRole(StrEnum):
    USER = "USER"
    ADMIN = "ADMIN"


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
