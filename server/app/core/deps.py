"""FastAPI 依赖统一出口：数据库会话、当前用户与管理员角色校验。"""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.common.enums import UserRole, UserStatus
from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """校验 JWT 并返回有效用户（实时查库，禁用用户立即失效）。"""
    if credentials is None:
        raise UnauthorizedError()
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload.get("sub"))
    except (InvalidTokenError, TypeError, ValueError):
        raise UnauthorizedError("登录已失效")

    user = db.get(User, user_id)
    if not user:
        raise UnauthorizedError("用户不存在")
    if user.status != UserStatus.ACTIVE.value:
        raise ForbiddenError("账号已被禁用")
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """校验当前用户为 ADMIN 角色。"""
    if user.role != UserRole.ADMIN.value:
        raise ForbiddenError("无权限访问")
    return user


__all__ = ["get_db", "get_current_user", "get_current_admin"]
