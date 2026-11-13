"""Redis 客户端（单例）。

用途：购物车、热点缓存、临时状态。Redis 仅作缓存/辅助，业务主数据以 MySQL 为准。
"""
import redis

from app.core.config import settings

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
    return _client
