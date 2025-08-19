from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
import json
import re
import logging

logger = logging.getLogger(__name__)


class SummaryRequest(BaseModel):
    """요약 요청 DTO - 줄바꿈 처리 완전 해결"""

    title: str = Field(..., min_length=1, max_length=200, description="요약 제목")
    input_data: str = Field(..., min_length=10, max_length=50000, description="요약할 텍스트")
    input_type: str = Field(default="text", description="입력 타입")
    summary_type: str = Field(default="general", description="요약 유형")
    file_url: Optional[str] = Field(None, description="파일 URL")

    @root_validator(pre=True)
    @classmethod
    def clean_all_text_fields(cls, values):
        """모든 텍스트 필드를 먼저 정리 (root_validator 사용)"""

        def clean_text(text: str) -> str:
            """텍스트 완전 정리"""
            if not text:
                return text

            logger.debug(f"정리 전 텍스트 길이: {len(text)}")
            logger.debug(f"정리 전 샘플: {repr(text[:50])}")

            # 1. 탭을 공백으로 변환
            text = text.replace('\t', ' ')

            # 2. 모든 종류의 줄바꿈을 공백으로 변환
            text = re.sub(r'\r\n|\r|\n', ' ', text)

            # 3. 연속된 공백을 하나로 정리
            text = re.sub(r'\s+', ' ', text)

            # 4. 제어 문자 완전 제거
            text = re.sub(r'[\x00-\x1F\x7F]', '', text)

            # 5. 앞뒤 공백 제거
            text = text.strip()

            logger.debug(f"정리 후 텍스트 길이: {len(text)}")
            logger.debug(f"정리 후 샘플: {repr(text[:50])}")

            return text

        # input_data 정리
        if 'input_data' in values and values['input_data']:
            values['input_data'] = clean_text(values['input_data'])

        # title 정리
        if 'title' in values and values['title']:
            values['title'] = clean_text(values['title'])

        return values

    @validator('input_data')
    @classmethod
    def validate_input_data(cls, v):
        """입력 데이터 최종 검증"""
        if not v or not v.strip():
            raise ValueError("입력 텍스트가 비어있습니다")

        # 정리 후 길이 재검증
        if len(v) < 10:
            raise ValueError("정리 후 텍스트가 너무 짧습니다 (최소 10자)")

        if len(v) > 50000:
            logger.warning(f"텍스트가 너무 길어서 자릅니다: {len(v)} -> 50000자")
            v = v[:50000]

        # 제어 문자가 남아있는지 최종 확인
        control_chars = [ord(c) for c in v if ord(c) < 32]
        if control_chars:
            logger.warning(f"제어 문자 발견됨: {control_chars}")
            # 혹시 남은 제어 문자가 있으면 다시 제거
            v = re.sub(r'[\x00-\x1F\x7F]', '', v)

        return v

    @validator('summary_type')
    @classmethod
    def validate_summary_type(cls, v):
        """요약 유형 검증"""
        allowed_types = ["general", "bullet_points", "key_insights", "brief", "detailed"]
        if v not in allowed_types:
            raise ValueError(f"허용되지 않은 요약 유형입니다. 사용 가능: {allowed_types}")
        return v

    @validator('title')
    @classmethod
    def validate_title(cls, v):
        """제목 최종 검증"""
        if not v or not v.strip():
            raise ValueError("제목이 비어있습니다")

        if len(v) > 200:
            raise ValueError("제목이 너무 깁니다 (최대 200자)")

        return v

    @validator('input_type')
    @classmethod
    def validate_input_type(cls, v):
        """입력 타입 검증"""
        allowed_types = ["text", "url", "file"]
        if v not in allowed_types:
            raise ValueError(f"허용되지 않은 입력 타입입니다. 사용 가능: {allowed_types}")
        return v

    @validator('file_url')
    @classmethod
    def validate_file_url(cls, v):
        """파일 URL 검증"""
        if v is not None and v.strip():
            # 기본적인 URL 형식 검증
            if not (v.startswith('http://') or v.startswith('https://')):
                raise ValueError("올바른 URL 형식이 아닙니다")
        return v

    class Config:
        """Pydantic 설정"""
        # 추가 필드 허용 안함
        extra = "forbid"

        # JSON 스키마에서 예제 포함
        schema_extra = {
            "example": {
                "title": "AWS 클라우드 서비스 요약",
                "input_data": "AWS는 컴퓨팅, 스토리지, 데이터베이스와 같은 인프라 기술부터 머신러닝까지 다양한 서비스를 제공합니다.",
                "input_type": "text",
                "summary_type": "general",
                "file_url": None
            }
        }


# 나머지 클래스들은 그대로 유지
class SummaryResponse(BaseModel):
    """요약 응답 DTO"""

    id: int
    user_id: int
    title: str
    input_type: str
    input_data: str
    summary_type: str
    output_data: str  # JSON 문자열
    file_url: Optional[str]
    created_at: str

    @validator('output_data')
    @classmethod
    def validate_output_data(cls, v):
        """출력 데이터가 유효한 JSON인지 확인"""
        if not v:
            return json.dumps({
                "summary": "",
                "key_points": [],
                "keywords": [],
                "error": "Empty output data"
            }, ensure_ascii=False)

        try:
            # JSON 파싱 테스트
            parsed = json.loads(v)

            # 기본 구조 검증
            if isinstance(parsed, dict):
                # 필수 필드가 있는지 확인
                if "summary" not in parsed:
                    parsed["summary"] = "요약 정보 없음"
                if "key_points" not in parsed:
                    parsed["key_points"] = []
                if "keywords" not in parsed:
                    parsed["keywords"] = []

                # 수정된 JSON 반환
                return json.dumps(parsed, ensure_ascii=False)
            else:
                # dict가 아니면 기본 구조로 래핑
                return json.dumps({
                    "summary": str(parsed),
                    "key_points": [],
                    "keywords": [],
                    "error": "Invalid structure"
                }, ensure_ascii=False)

        except json.JSONDecodeError:
            # JSON이 아닌 경우 기본 구조로 래핑
            return json.dumps({
                "summary": str(v)[:1000],  # 너무 길면 자름
                "key_points": [],
                "keywords": [],
                "error": "Invalid JSON format"
            }, ensure_ascii=False)

    @validator('created_at', pre=True)
    @classmethod
    def validate_created_at(cls, v):
        """생성일시 형식 검증"""
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)

    class Config:
        """Pydantic 설정"""
        # JSON 인코딩 시 한글 보존
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SummaryUpdate(BaseModel):
    """자료 요약 수정 DTO"""

    title: Optional[str] = Field(None, min_length=1, max_length=200, description="수정할 제목")
    summary_type: Optional[str] = Field(None, description="수정할 요약 유형")

    @validator('title')
    @classmethod
    def validate_title(cls, v):
        """제목 검증"""
        if v is not None:
            # 제목 정리
            v = re.sub(r'[\x00-\x1F\x7F]', ' ', v)
            v = re.sub(r'\s+', ' ', v).strip()

            if not v:
                raise ValueError("유효한 제목을 입력해주세요")
        return v

    @validator('summary_type')
    @classmethod
    def validate_summary_type(cls, v):
        """요약 유형 검증"""
        if v is not None:
            allowed_types = ["general", "bullet_points", "key_insights", "brief", "detailed"]
            if v not in allowed_types:
                raise ValueError(f"허용되지 않은 요약 유형입니다. 사용 가능: {allowed_types}")
        return v


class SummaryListResponse(BaseModel):
    """요약 목록 응답 DTO"""

    summaries: List[SummaryResponse]
    total_count: int
    page: int = Field(default=1, description="현재 페이지")
    page_size: int = Field(default=10, description="페이지 크기")
    has_next: bool = Field(default=False, description="다음 페이지 존재 여부")


class SummaryStats(BaseModel):
    """요약 통계 DTO"""

    total_summaries: int
    by_type: Dict[str, int] = Field(default_factory=dict, description="타입별 요약 수")
    by_date: Dict[str, int] = Field(default_factory=dict, description="날짜별 요약 수")
    avg_input_length: float = Field(default=0.0, description="평균 입력 텍스트 길이")
    avg_summary_length: float = Field(default=0.0, description="평균 요약 길이")