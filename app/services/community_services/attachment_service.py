from fastapi import HTTPException, UploadFile
from tortoise.transactions import in_transaction
from tortoise.functions import Sum
from app.core import s3
from app.core.s3 import head_object, public_url, delete_object, build_key
from app.core.attach_limits import *
from app.models.community import (
    PostModel, FreeImageModel, ShareFileModel, CategoryType
)

async def _get_counts_and_total(post_id: int) -> tuple[int, int]:
    img_cnt = await FreeImageModel.filter(post_id=post_id).count()
    file_cnt = await ShareFileModel.filter(post_id=post_id).count()
    img_sum = await FreeImageModel.filter(post_id=post_id).annotate(s=Sum("size_bytes")).values_list("s", flat=True)
    file_sum = await ShareFileModel.filter(post_id=post_id).annotate(s=Sum("size_bytes")).values_list("s", flat=True)
    total = (img_sum[0] or 0) + (file_sum[0] or 0)
    return img_cnt + file_cnt, total

def _ext_from_key(key: str) -> str:
    return key.rsplit(".", 1)[-1].lower() if "." in key else ""

def _validate_image_meta(key: str, meta: dict):
    ext = _ext_from_key(key)
    if ext not in IMAGE_EXTS:
        raise HTTPException(400, "Only jpg/png allowed")
    if meta.get("ContentType") not in IMAGE_MIMES:
        raise HTTPException(400, "Invalid image MIME")

def _validate_file_meta(key: str, meta: dict):
    ext = _ext_from_key(key)
    if ext not in FILE_EXTS:
        raise HTTPException(400, "Only pdf/docx allowed")
    if meta.get("ContentType") not in FILE_MIMES:
        raise HTTPException(400, "Invalid file MIME")

async def _ensure_author(post_id: int, user_id: int):
    post = await PostModel.get_or_none(id=post_id)
    if not post: raise HTTPException(404, "Post not found")
    if post.user_id != user_id: raise HTTPException(403, "Not the author")
    return post

async def upload_free_image(*, post_id: int, user_id: int, file: UploadFile) -> dict:
    # 권한/존재 확인
    post = await PostModel.get_or_none(id=post_id, category=CategoryType.FREE)
    if not post: raise HTTPException(404, "Post not found")
    if post.user_id != user_id: raise HTTPException(403, "Not the author")

    # 확장자/MIME 검증
    filename = file.filename or "upload.bin"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in IMAGE_EXTS or (file.content_type or "") not in IMAGE_MIMES:
        raise HTTPException(400, "Only jpg/png allowed")

    # 키 생성 후 S3 업로드 (스트리밍)
    key = build_key("free", filename)
    file.file.seek(0)
    s3.upload_fileobj(file.file, key, file.content_type or "application/octet-stream")

    # 사이즈/메타 확인
    meta = s3.head_object(key)  # {ContentLength, ContentType, ...}
    size = int(meta["ContentLength"])

    # 총 용량 제한 체크 (게시글당 10MB 등)
    current_total = await FreeImageModel.filter(post_id=post_id).sum("size_bytes") or 0
    if current_total + size > MAX_TOTAL_BYTES_PER_POST:
        # 초과 시 되돌리기
        s3.delete_object(key)
        raise HTTPException(413, "Total attachment size exceeded")

    # DB 반영
    async with in_transaction() as tx:
        img = await FreeImageModel.create(
            post_id=post_id,
            image_url=public_url(key),
            image_key=key,
            mime_type=meta.get("ContentType") or file.content_type,
            size_bytes=size,
            using_db=tx,
        )

    return {
        "id": img.id,
        "image_url": img.image_url,
        "mime_type": img.mime_type,
        "size_bytes": img.size_bytes,
    }

async def attach_free_image(*, post_id: int, user_id: int, key: str) -> dict:
    post = await _ensure_author(post_id, user_id)
    try:
        meta = head_object(key)
    except Exception:
        raise HTTPException(400, "S3 object not found or not accessible")

    _validate_image_meta(key, meta)
    size = int(meta.get("ContentLength", 0))
    if size <= 0:
        delete_object(key); raise HTTPException(400, "Empty image")

    cnt, total = await _get_counts_and_total(post_id)
    if cnt >= MAX_ATTACHMENTS_PER_POST:
        delete_object(key); raise HTTPException(400, f"Attachment count limit {MAX_ATTACHMENTS_PER_POST}")
    if total + size > MAX_TOTAL_BYTES_PER_POST:
        delete_object(key); raise HTTPException(400, "Total size exceeds 10MB")

    url = public_url(key)
    async with in_transaction():
        rec = await FreeImageModel.create(
            post_id=post_id, image_url=url, image_key=key,
            mime_type=meta.get("ContentType"), size_bytes=size
        )
    return {"id": rec.id, "image_url": rec.image_url, "mime_type": rec.mime_type, "size_bytes": rec.size_bytes}

async def attach_share_file(*, post_id: int, user_id: int, key: str) -> dict:
    post = await _ensure_author(post_id, user_id)
    try:
        meta = head_object(key)
    except Exception:
        raise HTTPException(400, "S3 object not found or not accessible")

    _validate_file_meta(key, meta)
    size = int(meta.get("ContentLength", 0))
    if size <= 0:
        delete_object(key); raise HTTPException(400, "Empty file")

    cnt, total = await _get_counts_and_total(post_id)
    if cnt >= MAX_ATTACHMENTS_PER_POST:
        delete_object(key); raise HTTPException(400, f"Attachment count limit {MAX_ATTACHMENTS_PER_POST}")
    if total + size > MAX_TOTAL_BYTES_PER_POST:
        delete_object(key); raise HTTPException(400, "Total size exceeds 10MB")

    url = public_url(key)
    async with in_transaction():
        rec = await ShareFileModel.create(
            post_id=post_id, file_url=url, file_key=key,
            mime_type=meta.get("ContentType"), size_bytes=size
        )
    return {"id": rec.id, "file_url": rec.file_url, "mime_type": rec.mime_type, "size_bytes": rec.size_bytes}

async def delete_free_image(*, post_id: int, user_id: int, image_id: int):
    await _ensure_author(post_id, user_id)
    rec = await FreeImageModel.get_or_none(id=image_id, post_id=post_id)
    if not rec: raise HTTPException(404, "Attachment not found")
    delete_object(rec.image_key)
    await rec.delete()
    return {"deleted": True}

async def delete_share_file(*, post_id: int, user_id: int, file_id: int):
    await _ensure_author(post_id, user_id)
    rec = await ShareFileModel.get_or_none(id=file_id, post_id=post_id)
    if not rec: raise HTTPException(404, "Attachment not found")
    delete_object(rec.file_key)
    await rec.delete()
    return {"deleted": True}
