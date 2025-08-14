from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

class SummaryRequest(BaseModel):
    """자료 요약 요청 DTO"""
    title: str = Field(..., description="요약 제목")
    input_data: str = Field(..., description="요약할 텍스트")
    input_type: Literal["text", "url", "file"] = Field(default="text", description="입력 타입")
    summary_type: Literal["general", "keywords", "qa", "study"] = Field(
        default="general",
        description="요약 유형"
    )
    file_url: Optional[str] = Field(None, description="파일 URL (파일 업로드 시)")

class SummaryResponse(BaseModel):
    """자료 요약 응답 DTO"""
    id: int
    user_id: int
    title: str
    input_type: str
    input_data: str
    summary_type: str
    output_data: str  # JSON 문자열
    file_url: Optional[str]
    created_at: datetime

class SummaryUpdate(BaseModel):
    """자료 요약 수정 DTO"""
    title: Optional[str] = None
    summary_type: Optional[str] = None