"""初始化脚本：幂等创建管理员、领养分类与演示领养宠物。

仅允许在 development/test 环境执行；生产环境直接拒绝。
管理员密码通过环境变量 ADMIN_SEED_PASSWORD 注入，不得写死在源码。

用法（在 server/ 目录下）：
    ADMIN_SEED_PASSWORD=你的密码 python -m scripts.seed
"""
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import AdoptionPetStatus, UserRole, UserStatus
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.pet import AdoptionPet, PetCategory
from app.models.user import User
from app.utils.time import utcnow

# (名称, 排序)
_CATEGORIES = [("猫", 1), ("狗", 2), ("其他", 3)]

# 演示领养宠物（均已上架）
_PETS = [
    ("猫", "小白", "中华田园猫", "MALE", 6, 2.5, "已驱虫、健康", True, True,
     "性格温顺亲人，喜欢晒太阳。", "北京", "有责任心，接受定期回访。",
     "一只活泼粘人的小白猫，已学会使用猫砂盆。"),
    ("猫", "花花", "英国短毛猫", "FEMALE", 12, 3.2, "健康、已绝育", True, True,
     "安静稳重，适合陪伴。", "上海", "有养猫经验者优先。",
     "蓝灰毛色的英短，亲人但不过分粘人。"),
    ("狗", "旺财", "中华田园犬", "MALE", 8, 8.0, "健康、已驱虫", True, False,
     "忠诚机警，看家护院好手。", "广州", "需要每天遛狗。",
     "机灵的小土狗，适应能力强。"),
    ("狗", "豆豆", "柯基", "FEMALE", 14, 10.0, "健康", True, True,
     "活泼好动，爱笑。", "深圳", "适合有院子的家庭。",
     "短腿大屁股的柯基，性格开朗。"),
    ("猫", "球球", "美国短毛猫", "MALE", 10, 3.5, "健康", True, True,
     "贪吃爱玩，喜欢逗猫棒。", "杭州", "按时喂食、定期体检。",
     "圆脸美短，虎斑花纹，非常上镜。"),
    ("狗", "大黄", "金毛寻回犬", "MALE", 24, 22.0, "健康、疫苗齐全", True, True,
     "温顺友善，适合有孩子的家庭。", "成都", "家庭养犬经验，较大活动空间。",
     "标准暖男金毛，服从性好。"),
    ("猫", "咪咪", "狸花猫", "FEMALE", 7, 2.1, "健康", False, False,
     "独立敏捷，捕鼠能手。", "武汉", "接受绝育承诺。",
     "漂亮的小狸花，性格独立又亲人。"),
    ("其他", "兔兔", "垂耳兔", "UNKNOWN", 4, 1.2, "健康", False, False,
     "温顺安静，爱吃草。", "南京", "准备合适的兔笼与干草。",
     "软萌垂耳兔，适合安静的领养人。"),
    ("猫", "雪球", "布偶猫", "FEMALE", 9, 3.0, "健康、已绝育", True, True,
     "黏人温柔，喜欢被抱。", "苏州", "室内散养，勤梳毛。",
     "蓝眼布偶，颜值与性格俱佳。"),
    ("狗", "黑子", "拉布拉多", "MALE", 18, 25.0, "健康", True, True,
     "聪明友善，服从性极佳。", "重庆", "有大型犬饲养经验优先。",
     "黑色拉布拉多，稳重可靠。"),
]


def seed_admin(db: Session) -> None:
    username = settings.admin_seed_username
    password = settings.admin_seed_password
    if not password:
        print("跳过管理员：未设置 ADMIN_SEED_PASSWORD（禁止空密码）。")
        return
    if len(password) < 6:
        print("错误：管理员密码至少 6 位。")
        sys.exit(1)

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
    print(f"管理员 '{username}' 创建成功。")


def seed_categories(db: Session) -> dict[str, PetCategory]:
    result: dict[str, PetCategory] = {}
    for name, sort in _CATEGORIES:
        existing = db.scalar(select(PetCategory).where(PetCategory.name == name))
        if existing:
            result[name] = existing
            continue
        cat = PetCategory(name=name, sort=sort, status="ACTIVE")
        db.add(cat)
        db.flush()
        result[name] = cat
        print(f"分类 '{name}' 创建成功。")
    return result


def seed_pets(db: Session, categories: dict[str, PetCategory]) -> None:
    created = 0
    for (
        cat_name, name, breed, gender, age_months, weight, health,
        vaccinated, neutered, personality, region, requirements, description,
    ) in _PETS:
        exists = db.scalar(select(AdoptionPet).where(AdoptionPet.name == name))
        if exists:
            continue
        pet = AdoptionPet(
            category_id=categories[cat_name].id,
            name=name,
            breed=breed,
            gender=gender,
            age_months=age_months,
            weight=weight,
            health_status=health,
            vaccinated=vaccinated,
            neutered=neutered,
            personality=personality,
            adoption_requirements=requirements,
            region=region,
            description=description,
            status=AdoptionPetStatus.AVAILABLE.value,
            published_at=utcnow(),
        )
        db.add(pet)
        created += 1
    print(f"演示领养宠物创建 {created} 条（幂等，已存在的跳过）。")


def main() -> None:
    if settings.is_production:
        print("拒绝执行：生产环境不允许自动初始化演示数据。")
        sys.exit(1)

    db = SessionLocal()
    try:
        seed_admin(db)
        categories = seed_categories(db)
        seed_pets(db, categories)
        db.commit()
        print("初始化数据完成。")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
