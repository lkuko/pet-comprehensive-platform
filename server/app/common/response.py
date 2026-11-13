"""统一响应结构。

成功统一返回 {"code": 0, "message": "success", "data": ...}。
code 为业务码（0 成功），HTTP status 表达协议层结果，二者不得混为一谈。
"""
from typing import Any

SUCCESS_CODE = 0
SUCCESS_MESSAGE = "success"


def ok(data: Any = None, message: str = SUCCESS_MESSAGE) -> dict[str, Any]:
    return {"code": SUCCESS_CODE, "message": message, "data": data}
