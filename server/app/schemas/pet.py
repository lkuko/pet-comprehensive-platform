"""用户宠物档案 Schema。"""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.common.enums import PetGender, PetSpecies
from app.utils.time import to_iso


class UserPetBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    category: PetSpecies = PetSpecies.OTHER
    breed: str | None = Field(default=None, max_length=80)
    gender: PetGender = PetGender.UNKNOWN
    birthday: date | None = None
    weight: float | None = Field(default=None, ge=0)
    avatar_url: str | None = Field(default=None, max_length=500)
    health_note: str | None = None
    is_neutered: bool = False


class UserPetCreate(UserPetBase):
    pass


class UserPetUpdate(BaseModel):
    """修改宠物档案；None 表示不修改该字段。"""

    name: str | None = Field(default=None, min_length=1, max_length=50)
    category: PetSpecies | None = None
    breed: str | None = Field(default=None, max_length=80)
    gender: PetGender | None = None
    birthday: date | None = None
    weight: float | None = Field(default=None, ge=0)
    avatar_url: str | None = Field(default=None, max_length=500)
    health_note: str | None = None
    is_neutered: bool | None = None


class UserPetOut(UserPetBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def _serialize_dt(self, dt: datetime, _info):
        return to_iso(dt)
