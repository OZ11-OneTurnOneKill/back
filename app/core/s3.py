import os
import boto3
from uuid import uuid4
from typing import BinaryIO

REGION  = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
BUCKET  = os.getenv("S3_BUCKET")
if not BUCKET:
    raise RuntimeError("S3_BUCKET is not set. Please set environment variable to your S3 bucket name.")

_session = boto3.session.Session(
    region_name=REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
_s3 = _session.client("s3")

def _ext(filename: str) -> str:
    return "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

def build_key(prefix: str, filename: str) -> str:
    return f"{prefix}/{uuid4().hex}{_ext(filename)}"

def public_url(key: str) -> str:
    base = os.getenv("S3_PUBLIC_BASE")
    return f"{base}/{key}" if base else f"https://{BUCKET}.s3.amazonaws.com/{key}"

def upload_fileobj(prefix: str, filename: str, fileobj: BinaryIO, content_type: str) -> dict:
    """
    서버가 받은 파일을 곧바로 S3에 업로드.
    """
    key = build_key(prefix, filename)
    _s3.upload_fileobj(
        Fileobj=fileobj,
        Bucket=BUCKET,
        Key=key,
        ExtraArgs={
            "ContentType": content_type,
            "ServerSideEncryption": "AES256",
        },
    )
    return {"key": key, "url": public_url(key)}

def delete_object(key: str):
    _s3.delete_object(Bucket=BUCKET, Key=key)
