from datetime import datetime
from typing import Optional, Literal, List

from pydantic import BaseModel


ApplicateStatus = Literal[
    "approved",
    "rejected",
]


class ApplicantSummary(BaseModel):
    application_id: int # 신청 게시글 아이디
    applicant_id: int # 신청자 아이디
    applicant_nickname: Optional[str] # 신청자 닉네임
    status: ApplicateStatus
    applied_at: datetime

class ApplicantListResponse(BaseModel):
    count: int
    next_cursor: Optional[int]
    items: List[ApplicantSummary]

class MyApplicationItem(BaseModel):
    application_id: int
    post_id: int
    post_title: Optional[str] = None
    post_category: str = "study"
    owner_id: int
    owner_nickname: Optional[str] = None
    status: ApplicateStatus
    applied_at: datetime
    updated_at: datetime

class MyApplicationListResponse(BaseModel):
    count: int
    next_cursor: Optional[int]
    items: List[MyApplicationItem]
