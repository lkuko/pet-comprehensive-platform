"""时间工具：统一 UTC 存取，业务时区 Asia/Shanghai。

约定：数据库 DATETIME 存「无时区的 UTC」，应用层读写统一按 UTC；
API 输出转带时区 ISO 8601，前端按 Asia/Shanghai 展示。
排班的「日期 + 时刻」是业务日历语义（DATE / TIME 直接存业务值），
组合成具体时间点时按业务时区解释，再转为无时区 UTC 保存。
"""
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

# 与 settings.app_timezone 保持一致（此处用常量避免与 config 循环依赖）
BUSINESS_TZ_NAME = "Asia/Shanghai"


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


def business_tz() -> ZoneInfo:
    """业务时区对象。"""
    return ZoneInfo(BUSINESS_TZ_NAME)


def combine_business_time(day: date, t: time) -> datetime:
    """业务时区的「日期 + 时刻」→ 无时区 UTC datetime。

    用于排班时段起止、预约时间点等具体时刻的落库。
    """
    local = datetime.combine(day, t, tzinfo=business_tz())
    return local.astimezone(timezone.utc).replace(tzinfo=None)


def to_utc_naive(dt: datetime) -> datetime:
    """任意 datetime（naive 按业务时区解释）→ 无时区 UTC datetime。

    用于接收用户提交的预约时间等具体时刻，统一转 UTC 落库。
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=business_tz())
    return dt.astimezone(timezone.utc).replace(tzinfo=None)
