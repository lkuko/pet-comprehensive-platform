"""存储抽象：隔离业务层与具体存储实现，未来可切换 OSS。"""
from typing import Protocol


class Storage(Protocol):
    """文件存储接口。save_image 返回可直接访问的相对 URL。"""

    def save_image(self, data: bytes, subdir: str, extension: str) -> str:
        """保存图片字节，返回相对 URL（如 /uploads/pets/xxx.jpg）。"""
        ...
