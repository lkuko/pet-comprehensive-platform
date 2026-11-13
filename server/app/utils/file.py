"""文件处理工具（图片上传使用）。

约定：文件名使用 UUID，原始文件名仅作元数据，不直接拼接磁盘路径。
"""
import uuid
from pathlib import Path

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
# 上传子目录白名单，防目录穿越
ALLOWED_UPLOAD_SUBDIRS = {"pets", "products", "avatars"}

_EXT_TO_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def random_filename(original: str) -> str:
    ext = Path(original).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"


def image_ext(filename: str) -> str:
    """返回规范化的小写扩展名；非法扩展名返回空字符串。"""
    ext = Path(filename).suffix.lower()
    return ext if ext in ALLOWED_IMAGE_EXT else ""
