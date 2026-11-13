"""业务单号生成器（Day 4 领养、Day 7 订单使用）。"""
import uuid
from datetime import datetime


def gen_no(prefix: str) -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}{ts}{uuid.uuid4().hex[:6].upper()}"
