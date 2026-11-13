"""认证相关 Schema。"""
from pydantic import BaseModel, Field

from app.schemas.user import UserOut


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=6, max_length=64)
    nickname: str | None = Field(default=None, min_length=1, max_length=50)
    phone: str | None = Field(default=None, max_length=20)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=64)


class TokenResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user: UserOut
