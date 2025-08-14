from .base_exception import NotFoundError, AccessDeniedError, BaseAppException


class SummaryException(BaseAppException):
    """요약 관련 기본 예외 클래스

    모든 요약 관련 예외의 부모 클래스입니다.
    요약 기능에서 발생하는 공통적인 처리를 담당합니다.

    이 클래스를 상속받으면 자동으로 요약 관련 예외임을
    나타내는 특별한 속성들을 갖게 됩니다.
    """

    def __init__(self, message: str, details: dict = None, error_code: str = None):
        """요약 예외 초기화

        Args:
            message: 사용자에게 보여질 오류 메시지
            details: 디버깅을 위한 상세 정보
            error_code: 클라이언트에서 구분하기 위한 코드
        """
        # 요약 관련 예외임을 나타내는 기본 정보 추가
        if details is None:
            details = {}

        details["service"] = "summary"  # 어떤 서비스에서 발생했는지 표시
        details["timestamp"] = details.get("timestamp")  # 발생 시간 기록 가능

        # error_code가 없으면 클래스명 기반으로 자동 생성
        if error_code is None:
            error_code = f"SUMMARY_{self.__class__.__name__.upper().replace('ERROR', '')}"

        super().__init__(message, details, error_code)


class SummaryNotFoundError(NotFoundError):
    """요약을 찾을 수 없을 때 발생하는 예외

    사용자가 존재하지 않는 요약 ID로 조회를 시도할 때 발생합니다.

    사용 예시:
        # 서비스에서
        if not summary:
            raise SummaryNotFoundError(summary_id)

        # API에서
        except SummaryNotFoundError as e:
            return 404, {"message": str(e)}
    """

    def __init__(self, summary_id: int):
        """요약 없음 예외 초기화

        Args:
            summary_id: 찾으려고 했던 요약의 ID
        """
        super().__init__("Summary", summary_id)

        # 추가적인 요약 관련 정보를 details에 포함
        self.details.update({
            "resource_name": "document_summary",  # 정확한 리소스명
            "suggested_action": "요약 목록에서 올바른 ID를 확인해주세요"
        })


class SummaryAccessDeniedError(AccessDeniedError):
    """요약 접근 권한이 없을 때 발생하는 예외

    사용자가 다른 사용자의 요약에 접근하려고 할 때 발생합니다.
    보안상 매우 중요한 예외로, 로그에 기록되어야 합니다.

    사용 예시:
        # 서비스에서
        if summary.user_id != user_id:
            raise SummaryAccessDeniedError(summary_id, user_id)
    """

    def __init__(self, summary_id: int, user_id: int):
        """접근 권한 없음 예외 초기화

        Args:
            summary_id: 접근하려던 요약의 ID
            user_id: 접근을 시도한 사용자의 ID
        """
        super().__init__("Summary", summary_id, user_id)

        # 보안 관련 추가 정보
        self.details.update({
            "security_level": "high",  # 보안 수준 표시
            "action_required": "access_log",  # 접근 로그 기록 필요
            "suggested_action": "본인의 요약만 접근할 수 있습니다"
        })


class SummaryCreationError(SummaryException):
    """요약 생성 실패 시 발생하는 예외

    AI 서비스 호출 실패, 데이터베이스 저장 실패 등
    요약 생성 과정에서 발생하는 모든 오류를 처리합니다.

    이 예외는 원인에 따라 다양한 HTTP 상태 코드로
    변환될 수 있습니다 (400, 500, 503 등).
    """

    def __init__(self, user_id: int, reason: str, original_error: Exception = None):
        """요약 생성 실패 예외 초기화

        Args:
            user_id: 요약을 생성하려던 사용자 ID
            reason: 실패 원인에 대한 설명
            original_error: 원본 예외 (있는 경우)
        """
        message = f"요약 생성에 실패했습니다: {reason}"

        details = {
            "user_id": user_id,
            "failure_reason": reason,
            "retry_possible": True,  # 재시도 가능 여부
        }

        # 원본 예외가 있다면 상세 정보에 포함
        if original_error:
            details.update({
                "original_error_type": type(original_error).__name__,
                "original_error_message": str(original_error),
                "stack_trace_available": True
            })

            # AI API 관련 오류인지 판단하여 재시도 가능성 결정
            if "rate limit" in str(original_error).lower():
                details["retry_possible"] = True
                details["suggested_wait_time"] = "60초 후 재시도"
            elif "quota" in str(original_error).lower():
                details["retry_possible"] = False
                details["suggested_action"] = "관리자에게 문의"

        super().__init__(message, details, "SUMMARY_CREATION_FAILED")


class SummaryValidationError(SummaryException):
    """요약 데이터 검증 실패 시 발생하는 예외

    사용자가 제공한 데이터가 요약 생성에 적합하지 않을 때 발생합니다.
    예: 너무 짧은 텍스트, 지원하지 않는 파일 형식 등
    """

    def __init__(self, field_errors: dict, user_input: str = None):
        """데이터 검증 실패 예외 초기화

        Args:
            field_errors: 필드별 오류 정보 딕셔너리
                예: {"input_data": "텍스트가 너무 짧습니다", "summary_type": "지원하지 않는 타입"}
            user_input: 사용자가 입력한 원본 데이터 (로깅용)
        """
        # 오류 메시지 생성 - 사용자 친화적으로 구성
        error_messages = []
        for field, error in field_errors.items():
            error_messages.append(f"{field}: {error}")

        message = "입력 데이터 검증에 실패했습니다. " + ", ".join(error_messages)

        details = {
            "field_errors": field_errors,
            "total_error_count": len(field_errors),
            "validation_type": "pre_processing"
        }

        # 사용자 입력이 있다면 통계 정보 추가 (개인정보 제외)
        if user_input:
            details.update({
                "input_length": len(user_input),
                "input_type_detected": "text" if isinstance(user_input, str) else "other",
                "contains_special_chars": any(not c.isalnum() and not c.isspace() for c in user_input[:100])
            })

        super().__init__(message, details, "SUMMARY_VALIDATION_FAILED")


class SummaryProcessingError(SummaryException):
    """요약 처리 과정에서 발생하는 예외

    AI가 응답을 생성했지만, 그 응답을 처리하는 과정에서
    문제가 발생했을 때 사용합니다.
    예: JSON 파싱 실패, 응답 구조 불일치 등
    """

    def __init__(self, processing_stage: str, error_details: str, ai_response: str = None):
        """처리 과정 오류 예외 초기화

        Args:
            processing_stage: 오류가 발생한 처리 단계 ("json_parsing", "validation", "formatting" 등)
            error_details: 구체적인 오류 내용
            ai_response: AI의 원본 응답 (디버깅용, 일부만 저장)
        """
        message = f"요약 처리 중 오류가 발생했습니다 ({processing_stage}): {error_details}"

        details = {
            "processing_stage": processing_stage,
            "error_details": error_details,
            "fallback_available": True,  # 폴백 응답 사용 가능
        }

        # AI 응답이 있다면 일부 정보만 저장 (너무 길어질 수 있으므로)
        if ai_response:
            details.update({
                "ai_response_length": len(ai_response),
                "ai_response_preview": ai_response[:200] + "..." if len(ai_response) > 200 else ai_response,
                "appears_to_be_json": ai_response.strip().startswith("{") and ai_response.strip().endswith("}")
            })

        super().__init__(message, details, "SUMMARY_PROCESSING_FAILED")


class SummaryContentError(SummaryException):
    """요약할 내용 자체에 문제가 있을 때 발생하는 예외

    사용자가 제공한 콘텐츠가 요약하기 어려운 상태일 때 발생합니다.
    예: 빈 내용, 의미없는 문자열, 너무 짧은 텍스트 등
    """

    def __init__(self, content_issue: str, content_length: int = 0, suggestions: list = None):
        """콘텐츠 문제 예외 초기화

        Args:
            content_issue: 콘텐츠의 구체적인 문제점
            content_length: 콘텐츠의 길이 (문자 수)
            suggestions: 사용자에게 제공할 개선 제안들
        """
        message = f"요약할 내용에 문제가 있습니다: {content_issue}"

        details = {
            "content_issue": content_issue,
            "content_length": content_length,
            "min_length_required": 50,  # 최소 요구 길이
            "max_length_supported": 50000,  # 최대 지원 길이
        }

        # 개선 제안이 제공되지 않았다면 기본 제안 생성
        if suggestions is None:
            suggestions = []
            if content_length < 50:
                suggestions.append("더 자세한 내용을 입력해주세요 (최소 50자)")
            if content_length > 50000:
                suggestions.append("내용을 나누어서 여러 번 요약해주세요")
            if not suggestions:
                suggestions.append("내용을 확인하고 다시 시도해주세요")

        details["suggestions"] = suggestions

        super().__init__(message, details, "SUMMARY_CONTENT_ERROR")


class SummaryQuotaExceededError(SummaryException):
    """요약 할당량 초과 시 발생하는 예외

    사용자가 일일/월간 요약 할당량을 초과했을 때 발생합니다.
    향후 유료 서비스나 사용량 제한 기능 추가 시 활용할 수 있습니다.
    """

    def __init__(self, user_id: int, current_usage: int, quota_limit: int, reset_time: str = None):
        """할당량 초과 예외 초기화

        Args:
            user_id: 사용자 ID
            current_usage: 현재 사용량
            quota_limit: 할당량 한도
            reset_time: 할당량 리셋 시간
        """
        message = f"요약 할당량을 초과했습니다 ({current_usage}/{quota_limit})"

        details = {
            "user_id": user_id,
            "current_usage": current_usage,
            "quota_limit": quota_limit,
            "usage_percentage": round((current_usage / quota_limit) * 100, 1),
        }

        if reset_time:
            details["quota_reset_time"] = reset_time
            message += f". 할당량은 {reset_time}에 리셋됩니다."

        super().__init__(message, details, "SUMMARY_QUOTA_EXCEEDED")


class SummaryFileTypeError(SummaryException):
    """지원하지 않는 파일 형식일 때 발생하는 예외

    향후 파일 업로드 요약 기능 추가 시 사용할 예외입니다.
    """

    def __init__(self, file_type: str, supported_types: list = None):
        """파일 형식 오류 예외 초기화

        Args:
            file_type: 업로드된 파일의 형식
            supported_types: 지원하는 파일 형식 목록
        """
        if supported_types is None:
            supported_types = ["pdf", "docx", "txt", "md"]

        message = f"지원하지 않는 파일 형식입니다: {file_type}"

        details = {
            "uploaded_file_type": file_type,
            "supported_file_types": supported_types,
            "suggestion": f"다음 형식 중 하나로 업로드해주세요: {', '.join(supported_types)}"
        }

        super().__init__(message, details, "SUMMARY_FILE_TYPE_ERROR")