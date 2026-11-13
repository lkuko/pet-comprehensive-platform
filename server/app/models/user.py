"""用户模型：账号、角色、状态与密码哈希。"""
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, PkType, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    phone: Mapped[str | None] = mapped_column(
        String(20), unique=True, nullable=True, index=True
    )
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="USER", index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)
