"""用户相关 Schema（与 ORM 分离）。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.utils.time import to_iso


class UserOut(BaseModel):
    """对外输出的用户信息（永不包含密码哈希）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str
    phone: str | None = None
    avatar_url: str | None = None
    role: str
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def _serialize_dt(self, dt: datetime, _info):
        return to_iso(dt)


class ProfileUpdate(BaseModel):
    """修改个人资料；None 表示不修改该字段，空字符串 phone 表示清空手机号。"""

    nickname: str | None = Field(default=None, min_length=1, max_length=50)
    phone: str | None = Field(default=None, max_length=20)
    avatar_url: str | None = Field(default=None, max_length=500)
