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


class AdoptionApplicationStatus(StrEnum):
    """领养申请状态机。

    PENDING → APPROVED / REJECTED / CANCELLED / CLOSED。
    CLOSED 表示同宠物其他申请已通过而自动关闭。
    """

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    CLOSED = "CLOSED"


class EnableStatus(StrEnum):
    """通用启用状态（医疗点/医生/医疗项目/排班复用）。"""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class MedicalAppointmentStatus(StrEnum):
    """医疗预约状态机。

    PENDING_CONFIRMATION → CONFIRMED / REJECTED / CANCELLED；
    CONFIRMED → COMPLETED。取消与拒绝均释放排班名额，完成后不再释放。
    """

    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
