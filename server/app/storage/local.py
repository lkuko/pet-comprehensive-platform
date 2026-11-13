"""本地文件存储实现（V1）。

文件名使用 UUID，原始文件名不参与磁盘路径拼接，防止目录穿越。
子目录由调用方传入，须经白名单校验。
"""
import uuid
from pathlib import Path

from app.core.config import settings


class LocalStorage:
    def __init__(self, base_dir: Path, base_url: str) -> None:
        self.base_dir = base_dir
        self.base_url = base_url.rstrip("/")

    def save_image(self, data: bytes, subdir: str, extension: str) -> str:
        target_dir = self.base_dir / subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex}{extension}"
        (target_dir / filename).write_bytes(data)
        return f"{self.base_url}/{subdir}/{filename}"


storage = LocalStorage(settings.upload_path, settings.upload_base_url)
