"""初始化脚本：幂等创建管理员账号。

仅允许在 development/test 环境执行；生产环境直接拒绝。
密码通过环境变量 ADMIN_SEED_PASSWORD 注入，不得写死在源码。

用法（在 server/ 目录下）：
    ADMIN_SEED_PASSWORD=你的密码 python -m scripts.seed
"""
import sys

from sqlalchemy import select

from app.common.enums import UserRole, UserStatus
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User


def seed_admin() -> None:
    if settings.is_production:
        print("拒绝执行：生产环境不允许自动创建默认管理员。")
        sys.exit(1)

    username = settings.admin_seed_username
    password = settings.admin_seed_password
    if not password:
        print("错误：请先设置环境变量 ADMIN_SEED_PASSWORD（禁止空密码）。")
        sys.exit(1)
    if len(password) < 6:
        print("错误：管理员密码至少 6 位。")
        sys.exit(1)

    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.username == username))
        if existing:
            print(f"管理员 '{username}' 已存在，跳过（幂等）。")
            return
        admin = User(
            username=username,
            password_hash=hash_password(password),
            nickname="管理员",
            role=UserRole.ADMIN.value,
            status=UserStatus.ACTIVE.value,
        )
        db.add(admin)
        db.commit()
        print(f"管理员 '{username}' 创建成功。")
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
