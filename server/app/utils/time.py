"""时间工具：统一 UTC 存取，业务时区 Asia/Shanghai。"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
