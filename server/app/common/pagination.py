"""统一分页模型与工具。"""
from typing import Any

from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.common.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class PageResult(BaseModel):
    """统一分页响应体。"""

    items: list[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE


def normalize_page(page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> tuple[int, int]:
    """规整分页参数：page 从 1 开始，page_size 有上限。"""
    page = max(1, page)
    page_size = min(max(1, page_size), MAX_PAGE_SIZE)
    return page, page_size


def paginate(db: Session, stmt: Select, page: int, page_size: int) -> PageResult:
    """执行 select 并返回分页结果，total 通过同条件 count 子查询获得。

    注意：仅适用于 select 返回单个 ORM 实体（scalar）的场景；
    多列/联表投影查询请在业务层自行封装。
    """
    page, page_size = normalize_page(page, page_size)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.limit(page_size).offset((page - 1) * page_size)).scalars().all()
    return PageResult(items=list(rows), total=total, page=page, page_size=page_size)
