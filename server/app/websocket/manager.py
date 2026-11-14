"""WebSocket 连接管理（V1 单实例，进程内）。

按管理员 ID 保存连接集合，供业务事务提交后广播即时提醒。
同步 Service（运行在线程池）通过 broadcast_sync 将协程调度回主事件循环。
广播失败仅记录日志，不回滚已提交的业务。
"""
import asyncio
import logging
import threading
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("app.websocket")


class AdminNotificationManager:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = {}
        self._loop: asyncio.AbstractEventLoop | None = None
        self._lock = threading.Lock()

    async def connect(self, admin_id: int, ws: WebSocket) -> None:
        with self._lock:
            self._connections.setdefault(admin_id, set()).add(ws)
        if self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                pass

    def disconnect(self, admin_id: int, ws: WebSocket) -> None:
        with self._lock:
            conns = self._connections.get(admin_id)
            if conns:
                conns.discard(ws)
                if not conns:
                    self._connections.pop(admin_id, None)

    async def _broadcast(self, payload: dict[str, Any]) -> None:
        with self._lock:
            targets = [ws for conns in self._connections.values() for ws in conns]
        for ws in targets:
            try:
                await ws.send_json(payload)
            except Exception:  # noqa: BLE001
                logger.warning("WebSocket 消息发送失败", exc_info=True)

    def broadcast_sync(self, payload: dict[str, Any]) -> None:
        """从同步上下文广播：调度到主事件循环执行，失败不影响业务。"""
        loop = self._loop
        if loop is None or loop.is_closed():
            return
        try:
            asyncio.run_coroutine_threadsafe(self._broadcast(payload), loop)
        except Exception:  # noqa: BLE001
            logger.warning("WebSocket 广播调度失败", exc_info=True)


notification_manager = AdminNotificationManager()
