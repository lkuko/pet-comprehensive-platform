"""上传相关 Schema。"""
from pydantic import BaseModel


class UploadResult(BaseModel):
    url: str
