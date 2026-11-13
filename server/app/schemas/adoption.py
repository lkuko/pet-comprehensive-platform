"""领养相关 Schema：分类、领养宠物、图片。"""
from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import AdoptionPetStatus, PetGender


class PetCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sort: int
    status: str


class AdoptionPetBase(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=50)
    breed: str | None = Field(default=None, max_length=80)
    gender: PetGender = PetGender.UNKNOWN
    age_months: int | None = Field(default=None, ge=0)
    weight: float | None = Field(default=None, ge=0)
    health_status: str = Field(default="", max_length=30)
    vaccinated: bool = False
    neutered: bool = False
    personality: str | None = None
    adoption_requirements: str = ""
    region: str = Field(default="", max_length=100)
    description: str = ""
    images: list[str] = Field(default_factory=list)


class AdoptionPetCreate(AdoptionPetBase):
    status: AdoptionPetStatus = AdoptionPetStatus.DRAFT


class AdoptionPetUpdate(BaseModel):
    """编辑领养宠物；None 表示不修改该字段（images=None 表示不动图片）。"""

    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=50)
    breed: str | None = Field(default=None, max_length=80)
    gender: PetGender | None = None
    age_months: int | None = Field(default=None, ge=0)
    weight: float | None = Field(default=None, ge=0)
    health_status: str | None = Field(default=None, max_length=30)
    vaccinated: bool | None = None
    neutered: bool | None = None
    personality: str | None = None
    adoption_requirements: str | None = None
    region: str | None = Field(default=None, max_length=100)
    description: str | None = None
    images: list[str] | None = None


class AdoptionPetStatusUpdate(BaseModel):
    status: AdoptionPetStatus


class AdoptionPetListItem(BaseModel):
    id: int
    name: str
    breed: str | None
    gender: str
    age_months: int | None
    weight: float | None
    region: str
    status: str
    category_id: int
    category_name: str | None
    cover_url: str | None
    published_at: str | None


class AdoptionPetDetail(AdoptionPetListItem):
    health_status: str
    vaccinated: bool
    neutered: bool
    personality: str | None
    adoption_requirements: str
    description: str
    images: list[str]
    created_at: str
    updated_at: str
