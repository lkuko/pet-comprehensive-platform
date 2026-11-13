"""业务状态枚举集中定义处。

约定：状态字段使用字符串枚举，避免前后端对数字状态含义不一致。
后续模块在此扩展（如 OrderStatus、AppointmentStatus）。
"""
from enum import StrEnum


class UserRole(StrEnum):
    USER = "USER"
    ADMIN = "ADMIN"


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class PetGender(StrEnum):
    """宠物性别。"""

    MALE = "MALE"
    FEMALE = "FEMALE"
    UNKNOWN = "UNKNOWN"


class PetSpecies(StrEnum):
    """用户宠物档案类别（猫/狗/其他）。"""

    CAT = "CAT"
    DOG = "DOG"
    OTHER = "OTHER"


class UserPetStatus(StrEnum):
    """用户宠物档案状态。"""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class AdoptionPetStatus(StrEnum):
    """领养宠物状态机：草稿 → 上架 → 下架/已领养。"""

    DRAFT = "DRAFT"
    AVAILABLE = "AVAILABLE"
    OFFLINE = "OFFLINE"
    ADOPTED = "ADOPTED"
