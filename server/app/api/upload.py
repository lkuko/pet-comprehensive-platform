"""通用图片上传接口（任意登录用户可用，覆盖头像/宠物/商品等场景）。"""
from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.common.response import ApiResponse
from app.core.config import settings
from app.core.deps import get_current_user
from app.core.exceptions import ParamError
from app.models.user import User
from app.schemas.upload import UploadResult
from app.storage import storage
from app.utils.file import ALLOWED_UPLOAD_SUBDIRS, image_ext

router = APIRouter(prefix="/upload", tags=["文件上传"])

# 明确非图片的 MIME 直接拒绝；octet-stream 等通用类型交由扩展名判定
_ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
_IGNORED_MIME = {"", "application/octet-stream"}


@router.post("/image", response_model=ApiResponse[UploadResult])
async def upload_image(
    file: UploadFile = File(...),
    subdir: str = Form("pets"),
    user: User = Depends(get_current_user),
):
    """上传单张图片，返回可访问的相对 URL。"""
    if subdir not in ALLOWED_UPLOAD_SUBDIRS:
        raise ParamError("不支持的图片分类")

    ext = image_ext(file.filename or "")
    if not ext:
        raise ParamError("仅支持 jpg/jpeg/png/webp 格式")

    if file.content_type not in _IGNORED_MIME and file.content_type not in _ALLOWED_MIME:
        raise ParamError("文件类型不合法")

    data = await file.read()
    if len(data) == 0:
        raise ParamError("空文件")
    if len(data) > settings.max_upload_size_mb * 1024 * 1024:
        raise ParamError(f"图片大小不能超过 {settings.max_upload_size_mb}MB")

    url = storage.save_image(data, subdir, ext)
    return ApiResponse(data=UploadResult(url=url))
