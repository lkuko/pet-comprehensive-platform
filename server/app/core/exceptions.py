"""统一业务异常。

code 为业务码，http_status 为协议层状态码，二者分工不同：
- 40001 参数错误、40100 未登录、40300 无权限、
- 40400 资源不存在、40900 状态冲突、50000 服务异常。
"""
from typing import Any


class BizError(Exception):
    """业务异常基类。"""

    def __init__(
        self,
        code: int,
        message: str,
        http_status: int = 400,
        data: Any = None,
    ) -> None:
        self.code = code
        self.message = message
        self.http_status = http_status
        self.data = data
        super().__init__(message)


class ParamError(BizError):
    def __init__(self, message: str = "参数错误", data: Any = None) -> None:
        super().__init__(40001, message, 400, data)


class UnauthorizedError(BizError):
    def __init__(self, message: str = "未登录或登录已失效") -> None:
        super().__init__(40100, message, 401)


class ForbiddenError(BizError):
    def __init__(self, message: str = "无权限访问") -> None:
        super().__init__(40300, message, 403)


class NotFoundError(BizError):
    def __init__(self, message: str = "资源不存在") -> None:
        super().__init__(40400, message, 404)


class ConflictError(BizError):
    def __init__(self, message: str = "状态冲突", data: Any = None) -> None:
        super().__init__(40900, message, 409, data)


class ServerError(BizError):
    def __init__(self, message: str = "服务异常") -> None:
        super().__init__(50000, message, 500)
