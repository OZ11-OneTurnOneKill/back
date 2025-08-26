"""학습계획 관련 예외들"""

from .base_exception import NotFoundError, AccessDeniedError, BaseAppException


class StudyPlanNotFoundError(NotFoundError):
    """학습계획을 찾을 수 없을 때 발생"""

    def __init__(self, study_plan_id: int):
        super().__init__("StudyPlan", study_plan_id)


class StudyPlanAccessDeniedError(AccessDeniedError):
    """학습계획 접근 권한이 없을 때 발생"""

    def __init__(self, study_plan_id: int, user_id: int):
        super().__init__("StudyPlan", study_plan_id, user_id)


class StudyPlanCreationError(BaseAppException):
    """학습계획 생성 실패 시 발생"""

    def __init__(self, user_id: int, reason: str):
        message = f"Failed to create study plan for user {user_id}: {reason}"
        details = {
            "user_id": user_id,
            "reason": reason
        }
        super().__init__(message, details, "CREATION_FAILED")


class StudyPlanValidationError(BaseAppException):
    """학습계획 데이터 검증 실패 시 발생"""

    def __init__(self, field_errors: dict):
        message = "Study plan validation failed"
        details = {"field_errors": field_errors}
        super().__init__(message, details, "VALIDATION_FAILED")