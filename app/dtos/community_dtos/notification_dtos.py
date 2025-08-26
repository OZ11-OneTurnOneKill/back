from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, conlist

class NotificationOut(BaseModel):
    id: int
    application_id: Optional[int] = None
    message: str
    is_read: bool
    created_at: datetime

class NotificationListResponse(BaseModel):
    count: int
    next_cursor: Optional[int] = Field(
        None, description="다음 페이지 요청용 커서(id). 없으면 마지막 페이지"
    )
    items: List[NotificationOut]

class MarkReadRequest(BaseModel):
    ids: conlist(int, min_length=1, max_length=100)
