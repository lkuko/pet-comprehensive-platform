"""通知相关 Schema。"""
from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    business_type: str
    business_id: int
    title: str
    content: str | None = None
    is_read: bool
    read_at: str | None = None
    created_at: str
