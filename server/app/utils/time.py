"""时间工具：统一 UTC 存取，业务时区 Asia/Shanghai。

约定：数据库 DATETIME 存「无时区的 UTC」，应用层读写统一按 UTC；
API 输出转带时区 ISO 8601，前端按 Asia/Shanghai 展示。
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """返回无时区的 UTC 当前时间（用于数据库写入）。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_iso(dt: datetime | None) -> str | None:
    """无时区 UTC → 带时区 ISO 8601（Z 结尾）。"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()
