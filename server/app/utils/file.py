"""文件处理工具（Day 3 图片上传使用）。

约定：文件名使用 UUID，原始文件名仅作元数据，不直接拼接磁盘路径。
"""
import uuid
from pathlib import Path

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def random_filename(original: str) -> str:
    ext = Path(original).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"
