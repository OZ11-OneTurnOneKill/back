"""기본 예외 클래스들"""


class BaseAppException(Exception):
    """애플리케이션 기본 예외 클래스

    모든 커스텀 예외의 부모 클래스입니다.
    공통 기능과 인터페이스를 제공합니다.
    """

    def __init__(self, message: str, details: dict = None, error_code: str = None):
        """예외 초기화

        Args:
            message: 에러 메시지
            details: 추가 정보 딕셔너리 (디버깅용)
            error_code: 에러 코드 (클라이언트 구분용)
        """
        self.message = message
        self.details = details or {}
        self.error_code = error_code
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """예외를 딕셔너리로 변환 (API 응답용)"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class NotFoundError(BaseAppException):
    """리소스를 찾을 수 없을 때 발생하는 예외"""

    def __init__(self, resource_type: str, resource_id: any):
        message = f"{resource_type} not found: {resource_id}"
        details = {
            "resource_type": resource_type,
            "resource_id": str(resource_id)
        }
        super().__init__(message, details, "NOT_FOUND")


class AccessDeniedError(BaseAppException):
    """접근 권한이 없을 때 발생하는 예외"""

    def __init__(self, resource_type: str, resource_id: any, user_id: any):
        message = f"Access denied to {resource_type} {resource_id} for user {user_id}"
        details = {
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "user_id": str(user_id)
        }
        super().__init__(message, details, "ACCESS_DENIED")