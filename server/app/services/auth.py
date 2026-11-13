"""认证业务：注册、登录、管理员登录。"""
from sqlalchemy.orm import Session

from app.common.enums import UserRole, UserStatus
from app.core.exceptions import ConflictError, ForbiddenError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserOut


def register(db: Session, data: RegisterRequest) -> TokenResponse:
    repo = UserRepository(db)
    if repo.get_by_username(data.username):
        raise ConflictError("用户名已存在")
    if data.phone and repo.get_by_phone(data.phone):
        raise ConflictError("手机号已被使用")

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        nickname=data.nickname or data.username,
        phone=data.phone or None,
        role=UserRole.USER.value,
        status=UserStatus.ACTIVE.value,
    )
    repo.add(user)
    db.commit()
    db.refresh(user)
    return _build_token(user)


def login(db: Session, data: LoginRequest) -> TokenResponse:
    user = _authenticate(db, data)
    return _build_token(user)


def admin_login(db: Session, data: LoginRequest) -> TokenResponse:
    user = _authenticate(db, data)
    if user.role != UserRole.ADMIN.value:
        raise ForbiddenError("非管理员账号")
    return _build_token(user)


def _authenticate(db: Session, data: LoginRequest) -> User:
    user = UserRepository(db).get_by_username(data.username)
    if not user or not verify_password(data.password, user.password_hash):
        raise UnauthorizedError("用户名或密码错误")
    if user.status != UserStatus.ACTIVE.value:
        raise ForbiddenError("账号已被禁用")
    return user


def _build_token(user: User) -> TokenResponse:
    return TokenResponse(token=create_access_token(user.id), user=UserOut.model_validate(user))
