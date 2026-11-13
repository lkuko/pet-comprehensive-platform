"""用户数据访问层：可复用查询封装。"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        return self.db.scalar(select(User).where(User.username == username))

    def get_by_phone(self, phone: str) -> User | None:
        return self.db.scalar(select(User).where(User.phone == phone))

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user
