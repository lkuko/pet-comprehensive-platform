"""初始化脚本：幂等创建管理员、领养分类/宠物、医疗资源与排班。

仅允许在 development/test 环境执行；生产环境直接拒绝。
管理员密码通过环境变量 ADMIN_SEED_PASSWORD 注入，不得写死在源码。

用法（在 server/ 目录下）：
    ADMIN_SEED_PASSWORD=你的密码 python -m scripts.seed
"""
import sys
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import AdoptionPetStatus, UserRole, UserStatus
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.care import CareServiceCategory, CareServicePackage
from app.models.mall import Product, ProductCategory
from app.models.medical import (
    DoctorSchedule,
    MedicalDoctor,
    MedicalLocation,
    MedicalService,
)
from app.models.pet import AdoptionPet, AdoptionPetImage, PetCategory
from app.models.user import User
from app.utils.time import business_tz, utcnow

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


# 演示领养宠物封面图（文件名位于 server/uploads/pets/ 下，seed 前需先放置图片）
_PET_IMAGES = {
    "小白": "pet-01.jpg",
    "花花": "pet-02.jpg",
    "旺财": "pet-03.jpg",
    "豆豆": "pet-04.jpg",
    "球球": "pet-05.jpg",
    "大黄": "pet-06.jpg",
    "咪咪": "pet-07.jpg",
    "兔兔": "pet-08.jpg",
    "雪球": "pet-09.jpg",
    "黑子": "pet-10.jpg",
}


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
        img = _PET_IMAGES.get(name)
        if img:
            pet.images.append(AdoptionPetImage(url=f"/uploads/pets/{img}", sort=0))
        created += 1
    # 回填既有演示宠物的封面图（幂等：仅当尚无图片时补充）
    for name, filename in _PET_IMAGES.items():
        pet = db.scalar(select(AdoptionPet).where(AdoptionPet.name == name))
        if pet and not pet.images:
            pet.images.append(AdoptionPetImage(url=f"/uploads/pets/{filename}", sort=0))
    print(f"演示领养宠物创建 {created} 条（幂等，已存在的跳过）。")


# 医疗点、医生、医疗项目（演示数据）
_MEDICAL_LOCATIONS = [
    ("爱宠宠物医院（总院）", "上海市徐汇区淮海西路 100 号", "021-88886666",
     "综合宠物医院，提供体检、疫苗、驱虫与基础诊疗预约。"),
    ("爱宠宠物医院（分院）", "上海市浦东新区张江路 200 号", "021-66668888",
     "社区型宠物诊所，提供常见病诊疗与免疫服务。"),
]

# (所属医疗点名称, 姓名, 职称, 擅长)
_MEDICAL_DOCTORS = [
    ("爱宠宠物医院（总院）", "张伟", "主治医师", "擅长犬猫内科、传染病诊治与免疫"),
    ("爱宠宠物医院（总院）", "李娜", "副主任医师", "擅长宠物外科手术与术后护理"),
    ("爱宠宠物医院（分院）", "王强", "执业兽医师", "擅长皮肤科、驱虫与日常保健"),
]

# (名称, 说明, 参考价, 时长分钟)
_MEDICAL_SERVICES = [
    ("基础体检", "血常规、体温、心肺听诊等基础检查", "99.00", 30),
    ("疫苗接种", "狂犬、猫三联/犬五联等疫苗接种", "150.00", 20),
    ("体内外驱虫", "体内外寄生虫预防与驱除", "80.00", 15),
]

# 排班时段模板（业务时区时刻）
_SCHEDULE_SLOTS = [(time(9, 0), time(10, 0)), (time(14, 0), time(15, 0))]
_SCHEDULE_DAYS = 7  # 未来 7 天
_SCHEDULE_CAPACITY = 3


def seed_medical(db: Session) -> None:
    """幂等创建医疗点、医生、医疗项目与未来 7 天排班。"""
    # 医疗点
    locations: dict[str, MedicalLocation] = {}
    for name, address, phone, desc in _MEDICAL_LOCATIONS:
        existing = db.scalar(select(MedicalLocation).where(MedicalLocation.name == name))
        if existing:
            locations[name] = existing
            continue
        loc = MedicalLocation(name=name, address=address, phone=phone, description=desc, status="ACTIVE")
        db.add(loc)
        db.flush()
        locations[name] = loc
        print(f"医疗点 '{name}' 创建成功。")

    # 医生
    doctors: dict[str, MedicalDoctor] = {}
    for loc_name, name, title, specialty in _MEDICAL_DOCTORS:
        existing = db.scalar(select(MedicalDoctor).where(MedicalDoctor.name == name))
        if existing:
            doctors[name] = existing
            continue
        doc = MedicalDoctor(
            location_id=locations[loc_name].id,
            name=name, title=title, specialty=specialty, status="ACTIVE",
        )
        db.add(doc)
        db.flush()
        doctors[name] = doc
        print(f"医生 '{name}' 创建成功。")

    # 医疗项目
    for name, desc, price, duration in _MEDICAL_SERVICES:
        existing = db.scalar(select(MedicalService).where(MedicalService.name == name))
        if existing:
            continue
        svc = MedicalService(
            name=name, description=desc, reference_price=price,
            duration_minutes=duration, status="ACTIVE",
        )
        db.add(svc)
        print(f"医疗项目 '{name}' 创建成功。")

    # 排班：每个医生生成未来 7 天排班（已存在未来排班则跳过该医生，保证幂等）
    today = datetime.now(business_tz()).date()
    created = 0
    for doc in doctors.values():
        has_future = db.scalar(
            select(DoctorSchedule.id).where(
                DoctorSchedule.doctor_id == doc.id,
                DoctorSchedule.schedule_date >= today,
            ).limit(1)
        )
        if has_future:
            continue
        for offset in range(1, _SCHEDULE_DAYS + 1):
            day = today + timedelta(days=offset)
            for start, end in _SCHEDULE_SLOTS:
                s = DoctorSchedule(
                    doctor_id=doc.id,
                    location_id=doc.location_id,
                    schedule_date=day,
                    start_time=start,
                    end_time=end,
                    capacity=_SCHEDULE_CAPACITY,
                    booked_count=0,
                    status="ACTIVE",
                )
                db.add(s)
                created += 1
    if created:
        print(f"医生排班创建 {created} 条（未来 {_SCHEDULE_DAYS} 天）。")
    else:
        print("医生排班已存在（未来排班），跳过。")


# 洗护/寄养分类与套餐（演示数据）
# (名称, 类型 GROOMING/BOARDING, 说明, 排序)
_CARE_CATEGORIES = [
    ("洗浴清洁", "GROOMING", "宠物基础洗浴、深层清洁与 SPA 护理", 1),
    ("美容造型", "GROOMING", "修剪造型、毛发护理与精致美容", 2),
    ("寄养", "BOARDING", "宠物短期寄养，提供住宿、喂食与遛弯", 3),
]

# (所属分类名称, 套餐名, 说明, 价格, 时长分钟；寄养时长为 0 表示按天计费)
_CARE_PACKAGES = [
    ("洗浴清洁", "基础洗浴", "常规洗浴 + 吹干 + 耳道清洁", "50.00", 40),
    ("洗浴清洁", "深层清洁", "深层清洁 + 护毛素 + 指甲修剪", "120.00", 70),
    ("美容造型", "基础美容", "修剪 + 造型 + 基础护理", "150.00", 90),
    ("美容造型", "精致造型", "精致修剪 + 造型 + SPA", "260.00", 120),
    ("寄养", "标准寄养", "标准笼舍 + 每日喂食 + 遛弯", "60.00", 0),
    ("寄养", "豪华寄养", "独立房 + 每日视频 + 营养餐", "100.00", 0),
]


def seed_care(db: Session) -> None:
    """幂等创建洗护/寄养分类与套餐。"""
    categories: dict[str, CareServiceCategory] = {}
    for name, service_type, desc, sort in _CARE_CATEGORIES:
        existing = db.scalar(
            select(CareServiceCategory).where(CareServiceCategory.name == name)
        )
        if existing:
            categories[name] = existing
            continue
        cat = CareServiceCategory(
            name=name, service_type=service_type, description=desc,
            sort=sort, status="ACTIVE",
        )
        db.add(cat)
        db.flush()
        categories[name] = cat
        print(f"服务分类 '{name}' 创建成功。")

    created = 0
    for cat_name, name, desc, price, duration in _CARE_PACKAGES:
        existing = db.scalar(
            select(CareServicePackage).where(CareServicePackage.name == name)
        )
        if existing:
            continue
        pkg = CareServicePackage(
            category_id=categories[cat_name].id,
            name=name, description=desc, price=price,
            duration_minutes=duration, status="ACTIVE",
        )
        db.add(pkg)
        created += 1
    if created:
        print(f"服务套餐创建 {created} 条（幂等，已存在的跳过）。")
    else:
        print("服务套餐已存在，跳过。")


# 商城分类与商品（演示数据）
# (名称, 说明, 排序)
_MALL_CATEGORIES = [
    ("猫粮", "猫咪主粮、罐头与零食", 1),
    ("狗粮", "犬用主粮、罐头与零食", 2),
    ("日用品", "猫砂、尿垫、食盆等日常用品", 3),
    ("玩具", "逗猫棒、磨牙玩具等互动玩具", 4),
]

# (所属分类名称, 商品名, 副标题, 描述, 价格, 库存)
_MALL_PRODUCTS = [
    ("猫粮", "全价成猫粮 2kg", "高蛋白无谷配方", "鸡肉味全价猫粮，营养均衡", "88.00", 500),
    ("猫粮", "猫罐头 85g×12罐", "湿粮补水", "吞拿鱼口味主食罐，开罐即食", "60.00", 300),
    ("狗粮", "全价犬粮 5kg", "成犬营养", "牛肉味全价犬粮，含益生菌", "120.00", 200),
    ("日用品", "豆腐猫砂 6L", "结团除臭", "可冲厕所豆腐猫砂，低尘除臭", "35.00", 400),
    ("日用品", "宠物尿垫 100片", "加厚吸水", "XL 加厚吸水尿垫，锁水防漏", "55.00", 250),
    ("玩具", "逗猫棒套装", "互动逗猫", "羽毛替换头逗猫棒，猫咪最爱", "25.00", 150),
]


# 演示商品封面图（文件名位于 server/uploads/products/ 下）
_PRODUCT_IMAGES = {
    "全价成猫粮 2kg": "product-01.jpg",
    "猫罐头 85g×12罐": "product-02.jpg",
    "全价犬粮 5kg": "product-03.jpg",
    "豆腐猫砂 6L": "product-04.jpg",
    "宠物尿垫 100片": "product-05.jpg",
    "逗猫棒套装": "product-06.jpg",
}


def seed_mall(db: Session) -> None:
    """幂等创建商城分类与商品。"""
    categories: dict[str, ProductCategory] = {}
    for name, desc, sort in _MALL_CATEGORIES:
        existing = db.scalar(select(ProductCategory).where(ProductCategory.name == name))
        if existing:
            categories[name] = existing
            continue
        cat = ProductCategory(name=name, description=desc, sort=sort, status="ACTIVE")
        db.add(cat)
        db.flush()
        categories[name] = cat
        print(f"商品分类 '{name}' 创建成功。")

    created = 0
    for cat_name, name, subtitle, desc, price, stock in _MALL_PRODUCTS:
        existing = db.scalar(select(Product).where(Product.name == name))
        if existing:
            continue
        p = Product(
            category_id=categories[cat_name].id,
            name=name, subtitle=subtitle, description=desc,
            price=price, stock=stock, sales=0, status="ACTIVE",
            cover_image=f"/uploads/products/{_PRODUCT_IMAGES[name]}" if name in _PRODUCT_IMAGES else None,
        )
        db.add(p)
        created += 1
    # 回填既有商品的封面图（幂等：仅当尚无封面时补充）
    for name, filename in _PRODUCT_IMAGES.items():
        p = db.scalar(select(Product).where(Product.name == name))
        if p and not p.cover_image:
            p.cover_image = f"/uploads/products/{filename}"
    if created:
        print(f"商品创建 {created} 条（幂等，已存在的跳过）。")
    else:
        print("商品已存在，跳过。")


def main() -> None:
    if settings.is_production:
        print("拒绝执行：生产环境不允许自动初始化演示数据。")
        sys.exit(1)

    db = SessionLocal()
    try:
        seed_admin(db)
        categories = seed_categories(db)
        seed_pets(db, categories)
        seed_medical(db)
        seed_care(db)
        seed_mall(db)
        db.commit()
        print("初始化数据完成。")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
