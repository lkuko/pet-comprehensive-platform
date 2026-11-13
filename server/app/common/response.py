"""统一响应结构。

成功统一返回 {"code": 0, "message": "success", "data": ...}。
code 为业务码（0 成功），HTTP status 表达协议层结果，二者不得混为一谈。
"""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

SUCCESS_CODE = 0
SUCCESS_MESSAGE = "success"

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一响应信封（供 response_model 使用，生成 OpenAPI 文档）。"""

    code: int = SUCCESS_CODE
    message: str = SUCCESS_MESSAGE
    data: T | None = None


def ok(data: Any = None, message: str = SUCCESS_MESSAGE) -> dict[str, Any]:
    return {"code": SUCCESS_CODE, "message": message, "data": data}
