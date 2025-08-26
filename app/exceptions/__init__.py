"""예외 패키지 통합 import

이 모듈은 프로젝트 전체에서 사용하는 모든 예외 클래스를
한 곳에서 관리합니다.

사용법:
    from app.exceptions import SummaryNotFoundError, StudyPlanNotFoundError

    # 또는 특정 카테고리만
    from app.exceptions.summary import SummaryCreationError
"""

# 기본 예외들
from .base_exception import (
    BaseAppException,
    NotFoundError,
    AccessDeniedError
)

# 학습계획 관련 예외들 (기존)
from .study_plan_exception import (
    StudyPlanNotFoundError,
    StudyPlanAccessDeniedError,
    StudyPlanCreationError,
    StudyPlanValidationError
)

# 🔥 새로 추가: 요약 관련 예외들
from .summary_exception import (
    SummaryException,
    SummaryNotFoundError,
    SummaryAccessDeniedError,
    SummaryCreationError,
    SummaryValidationError,
    SummaryProcessingError,
    SummaryContentError,
    SummaryQuotaExceededError,
    SummaryFileTypeError
)

# 편의를 위한 전체 목록
__all__ = [
    # 기본 예외들
    "BaseAppException",
    "NotFoundError",
    "AccessDeniedError",

    # 학습계획 예외들
    "StudyPlanNotFoundError",
    "StudyPlanAccessDeniedError",
    "StudyPlanCreationError",
    "StudyPlanValidationError",

    # 🔥 요약 예외들
    "SummaryException",
    "SummaryNotFoundError",
    "SummaryAccessDeniedError",
    "SummaryCreationError",
    "SummaryValidationError",
    "SummaryProcessingError",
    "SummaryContentError",
    "SummaryQuotaExceededError",
    "SummaryFileTypeError",
]

# 예외 매핑 딕셔너리 - 에러 코드로 예외 클래스 찾기
EXCEPTION_MAP = {
    # 요약 관련
    "SUMMARY_NOT_FOUND": SummaryNotFoundError,
    "SUMMARY_ACCESS_DENIED": SummaryAccessDeniedError,
    "SUMMARY_CREATION_FAILED": SummaryCreationError,
    "SUMMARY_VALIDATION_FAILED": SummaryValidationError,
    "SUMMARY_PROCESSING_FAILED": SummaryProcessingError,
    "SUMMARY_CONTENT_ERROR": SummaryContentError,
    "SUMMARY_QUOTA_EXCEEDED": SummaryQuotaExceededError,
    "SUMMARY_FILE_TYPE_ERROR": SummaryFileTypeError,

    # 학습계획 관련 (기존)
    "STUDY_PLAN_NOT_FOUND": StudyPlanNotFoundError,
    "STUDY_PLAN_ACCESS_DENIED": StudyPlanAccessDeniedError,
    "STUDY_PLAN_CREATION_FAILED": StudyPlanCreationError,
}

def get_exception_by_code(error_code: str) -> type:
    """에러 코드로 예외 클래스를 찾는 헬퍼 함수

    Args:
        error_code: 찾고자 하는 에러 코드

    Returns:
        해당하는 예외 클래스, 없으면 BaseAppException

    사용 예시:
        exception_class = get_exception_by_code("SUMMARY_NOT_FOUND")
        raise exception_class("메시지")
    """
    return EXCEPTION_MAP.get(error_code, BaseAppException)