"""管理端业务通知模型。

表：admin_notifications（待处理通知记录）。WebSocket 仅负责即时提醒，
未读列表以本表为准，二者解耦，避免漏消息。
"""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, PkType, TimestampMixin


class AdminNotification(Base, TimestampMixin):
    __tablename__ = "admin_notifications"
    __table_args__ = (Index("ix_admin_notifications_read", "is_read", "created_at"),)

    id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    business_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    business_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
