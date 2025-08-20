from io import BytesIO
from typing import Optional
from fastapi import HTTPException, UploadFile
from tortoise.transactions import in_transaction
from tortoise.functions import Sum
from app.core.s3 import upload_fileobj, delete_object
from app.core.attach_limits import (
    MAX_ATTACHMENTS_PER_POST, MAX_TOTAL_BYTES_PER_POST,
    IMAGE_EXTS, IMAGE_MIMES, FILE_EXTS, FILE_MIMES
)
from app.models.community import (
    PostModel, FreeImageModel, ShareFileModel, CategoryType
)


def _bad_request(msg: str):
    raise HTTPException(status_code=400, detail=msg)

def _ext(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

async def _current_count_and_total(post_id: int, kind: str) -> tuple[int, int]:
    """
    kind: "free" | "share"
    """
    if kind == "free":
        qs = FreeImageModel.filter(post_id=post_id)
    else:
        qs = ShareFileModel.filter(post_id=post_id)

    count = await qs.count()
    total_row = await qs.annotate(total=Sum("size_bytes")).values("total")
    total = int(total_row[0]["total"]) if total_row and total_row[0]["total"] is not None else 0
    return count, total

async def upload_free_image(*, post_id: int, user_id: int, file: UploadFile) -> dict:
    # 소유자/카테고리 확인
    post = await PostModel.get_or_none(id=post_id, category=CategoryType.FREE)
    if not post:
        raise HTTPException(404, "Post not found")
    if post.user_id != user_id:
        raise HTTPException(403, "Not the author")

    # 확장자/타입 체크
    ext = _ext(file.filename or "")
    if ext not in IMAGE_EXTS:
        _bad_request("Only jpg/png allowed")
    if (file.content_type or "").lower() not in IMAGE_MIMES:
        _bad_request("Invalid Content-Type for image")

    # 크기 체크 (메모리 10MB 이내라면 안전)
    data = await file.read()
    size = len(data)
    if size == 0:
        _bad_request("Empty file")

    # 개수/총용량 제한
    count, total = await _current_count_and_total(post_id, "free")
    if count >= MAX_ATTACHMENTS_PER_POST:
        _bad_request("Max 10 images per post")
    if total + size > MAX_TOTAL_BYTES_PER_POST:
        _bad_request("Total size per post exceeds 10MB")

    # S3 업로드
    up = upload_fileobj(prefix="free", filename=file.filename, fileobj=BytesIO(data), content_type=file.content_type)

    # DB 저장
    async with in_transaction() as tx:
        img = await FreeImageModel.create(
            post_id=post_id,
            image_url=up["url"],
            image_key=up["key"],
            mime_type=file.content_type,
            size_bytes=size,
            using_db=tx,
        )
    return {
        "id": img.id,
        "image_url": img.image_url,
        "mime_type": img.mime_type,
        "size_bytes": img.size_bytes,
    }

async def delete_free_image(*, post_id: int, user_id: int, image_id: int) -> dict:
    post = await PostModel.get_or_none(id=post_id, category=CategoryType.FREE)
    if not post:
        raise HTTPException(404, "Post not found")
    if post.user_id != user_id:
        raise HTTPException(403, "Not the author")

    img = await FreeImageModel.get_or_none(id=image_id, post_id=post_id)
    if not img:
        raise HTTPException(404, "Image not found")

    # S3 삭제 + DB 삭제
    delete_object(img.image_key)
    await img.delete()
    return {"ok": True}

async def upload_share_file(*, post_id: int, user_id: int, file: UploadFile) -> dict:
    post = await PostModel.get_or_none(id=post_id, category=CategoryType.SHARE)
    if not post:
        raise HTTPException(404, "Post not found")
    if post.user_id != user_id:
        raise HTTPException(403, "Not the author")

    ext = _ext(file.filename or "")
    if ext not in FILE_EXTS:
        _bad_request("Only pdf/docx allowed")
    if (file.content_type or "").lower() not in FILE_MIMES:
        _bad_request("Invalid Content-Type for file")

    data = await file.read()
    size = len(data)
    if size == 0:
        _bad_request("Empty file")

    count, total = await _current_count_and_total(post_id, "share")
    if count >= MAX_ATTACHMENTS_PER_POST:
        _bad_request("Max 10 files per post")
    if total + size > MAX_TOTAL_BYTES_PER_POST:
        _bad_request("Total size per post exceeds 10MB")

    up = upload_fileobj(prefix="share", filename=file.filename, fileobj=BytesIO(data), content_type=file.content_type)

    async with in_transaction() as tx:
        f = await ShareFileModel.create(
            post_id=post_id,
            file_url=up["url"],
            file_key=up["key"],
            original_filename=file.filename or "",
            mime_type=file.content_type,
            size_bytes=size,
            using_db=tx,
        )
    return {
        "id": f.id,
        "file_url": f.file_url,
        "original_filename": f.original_filename,
        "mime_type": f.mime_type,
        "size_bytes": f.size_bytes,
    }

async def delete_share_file(*, post_id: int, user_id: int, file_id: int) -> dict:
    post = await PostModel.get_or_none(id=post_id, category=CategoryType.SHARE)
    if not post:
        raise HTTPException(404, "Post not found")
    if post.user_id != user_id:
        raise HTTPException(403, "Not the author")

    f = await ShareFileModel.get_or_none(id=file_id, post_id=post_id)
    if not f:
        raise HTTPException(404, "File not found")

    delete_object(f.file_key)
    await f.delete()
    return {"ok": True}
