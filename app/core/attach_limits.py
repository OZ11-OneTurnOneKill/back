from typing import Final

# 게시글 첨부 제한
MAX_ATTACHMENTS_PER_POST: Final[int] = 10
MAX_TOTAL_BYTES_PER_POST: Final[int] = 15 * 1024 * 1024

# 허용 확장자 / MIME
IMAGE_EXTS = {"jpg", "jpeg", "png"}
IMAGE_MIMES = {"image/jpeg", "image/png"}

FILE_EXTS = {"pdf", "docx"}
FILE_MIMES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}