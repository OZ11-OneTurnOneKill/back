from typing import Dict
from pydantic import BaseModel, Field, ConfigDict

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