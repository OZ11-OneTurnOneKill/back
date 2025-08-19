import os
from uuid import uuid4
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

REGION  = os.getenv("AWS_REGION", "ap-northeast-2")
BUCKET  = os.getenv("S3_BUCKET")
EXPIRES = int(os.getenv("S3_PRESIGN_EXPIRES", "600"))

if not BUCKET:
    raise RuntimeError("S3_BUCKET is not set. Please set environment variable to your S3 bucket name.")

# ▶ 크레덴셜은 "기본 체인" 사용: EC2 Role(인스턴스 프로필) 우선, 없으면 환경변수/프로파일 등
_session = boto3.session.Session(region_name=REGION)
_s3 = _session.client(
    "s3",
    config=Config(s3={"addressing_style": "virtual"})  # https://{bucket}.s3.{region}.amazonaws.com 형태
)

def _ext(filename: str) -> str:
    return "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

def build_key(prefix: str, filename: str) -> str:
    return f"{prefix}/{uuid4().hex}{_ext(filename)}"

def presigned_post_strict(prefix: str, filename: str, content_type: str, max_bytes: int):
    """
    - key, Content-Type, max size를 '조건'으로 고정한 presigned POST 발급
    - 반환 url은 리전 호스트로 강제 (UX/네트워크 경로 명확화)
    """
    key = build_key(prefix, filename)
    fields = {
        "Content-Type": content_type,
        "x-amz-server-side-encryption": "AES256",
    }
    conditions = [
        {"x-amz-server-side-encryption": "AES256"},
        ["content-length-range", 0, max_bytes],
        ["eq", "$Content-Type", content_type],
        ["eq", "$key", key],
        {"bucket": BUCKET},
    ]
    form = _s3.generate_presigned_post(
        Bucket=BUCKET, Key=key, Fields=fields, Conditions=conditions, ExpiresIn=EXPIRES
    )
    # botocore가 주는 url은 글로벌일 수 있어 리전 호스트로 교체
    url = f"https://{BUCKET}.s3.{REGION}.amazonaws.com/"
    return {"key": key, "url": url, "fields": form["fields"], "expires_in": EXPIRES}

def head_object(key: str):
    """
    업로드 검증용. 존재/권한 문제면 None 반환(라우터/서비스에서 400 처리).
    다른 오류는 그대로 raise.
    """
    try:
        return _s3.head_object(Bucket=BUCKET, Key=key)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("404", "NoSuchKey", "403", "AccessDenied"):
            return None
        raise

def public_url(key: str) -> str:
    """
    공개 호스팅 베이스가 지정되면 그걸 사용, 아니면 리전 호스트 사용
    """
    base = os.getenv("S3_PUBLIC_BASE")
    if base:
        return f"{base.rstrip('/')}/{key}"
    return f"https://{BUCKET}.s3.{REGION}.amazonaws.com/{key}"

def delete_object(key: str):
    _s3.delete_object(Bucket=BUCKET, Key=key)


def upload_fileobj(fileobj, key: str, content_type: str):
    _s3.upload_fileobj(
        Fileobj=fileobj,
        Bucket=BUCKET,
        Key=key,
        ExtraArgs={"ContentType": content_type, "ServerSideEncryption": "AES256"},
    )
