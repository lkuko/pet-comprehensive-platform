"""统一响应结构与业务异常元数据的单元测试。"""
from app.common.response import ok
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ParamError,
    UnauthorizedError,
)


def test_ok_shape():
    assert ok({"id": 1}) == {"code": 0, "message": "success", "data": {"id": 1}}


def test_exception_code_mapping():
    assert ParamError().code == 40001
    assert UnauthorizedError().code == 40100
    assert ForbiddenError().code == 40300
    assert NotFoundError().code == 40400
    assert ConflictError().code == 40900


def test_conflict_error_meta():
    err = ConflictError("该宠物已被领养")
    assert err.code == 40900
    assert err.http_status == 409
    assert err.message == "该宠物已被领养"
