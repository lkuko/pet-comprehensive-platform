"""用户资料业务。"""
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import ProfileUpdate, UserOut


def get_profile(db: Session, user_id: int) -> UserOut:
    return UserOut.model_validate(_get_or_404(db, user_id))


def update_profile(db: Session, user_id: int, data: ProfileUpdate) -> UserOut:
    repo = UserRepository(db)
    user = _get_or_404(db, user_id)

    if data.nickname is not None:
        user.nickname = data.nickname
    if data.phone is not None:
        new_phone = data.phone or None
        if new_phone and new_phone != user.phone:
            existing = repo.get_by_phone(new_phone)
            if existing and existing.id != user.id:
                raise ConflictError("手机号已被使用")
        user.phone = new_phone
    if data.avatar_url is not None:
        user.avatar_url = data.avatar_url

    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


def _get_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise NotFoundError("用户不存在")
    return user
