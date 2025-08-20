from typing import Dict
from pydantic import BaseModel, Field, ConfigDict, AnyUrl


class PresignReq(BaseModel):
    model_config = ConfigDict(extra='forbid')
    filename: str = Field(min_length=1, max_length=255)
    content_type: str

class PresignResp(BaseModel):
    model_config = ConfigDict(extra='forbid')
    key: str
    url: str
    fields: Dict[str, str]   # presigned form fields
    expires_in: int

class AttachReq(BaseModel):
    model_config = ConfigDict(extra='forbid')
    key: str


class FreeImageItem(BaseModel):
    id: int
    image_url: AnyUrl | str
    mime_type: str
    size_bytes: int

class ShareFileItem(BaseModel):
    id: int
    file_url: AnyUrl | str
    original_filename: str
    mime_type: str
    size_bytes: int