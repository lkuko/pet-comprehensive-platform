"""WebSocket 管理端业务提醒端点。

地址：/ws/admin/notifications（不带 /api/v1 前缀）。
连接建立后客户端须在 5 秒内发送认证首帧 {"token": "<access_token>"}，
服务端校验 JWT 且角色为 ADMIN 后才注册连接，否则立即关闭。
"""
import asyncio
import json
import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.common.enums import UserRole, UserStatus
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.websocket.manager import notification_manager

logger = logging.getLogger("app.websocket.notifications")

router = APIRouter()


def _authenticate_admin(db: Session, token: str) -> int | None:
    """校验 Token 并返回管理员 ID；失败返回 None。"""
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except (InvalidTokenError, TypeError, ValueError):
        return None
    user = db.get(User, user_id)
    if not user or user.role != UserRole.ADMIN.value or user.status != UserStatus.ACTIVE.value:
        return None
    return user.id


@router.websocket("/ws/admin/notifications")
async def admin_notifications(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    admin_id: int | None = None
    try:
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
        token = ""
        try:
            token = json.loads(raw).get("token", "")
        except (json.JSONDecodeError, AttributeError):
            token = ""
        admin_id = _authenticate_admin(db, token)
        if admin_id is None:
            await websocket.close(code=1008, reason="未认证")
            return
        await notification_manager.connect(admin_id, websocket)

        # 保持连接，接收客户端心跳/消息（内容忽略），断开时清理
        while True:
            await websocket.receive_text()
    except (asyncio.TimeoutError, WebSocketDisconnect):
        pass
    except Exception:  # noqa: BLE001
        logger.warning("WebSocket 连接异常", exc_info=True)
    finally:
        if admin_id is not None:
            notification_manager.disconnect(admin_id, websocket)
