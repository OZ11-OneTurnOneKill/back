# Custom Exception Classes for the Application

class BaseStudyPlanException(Exception):
    """Base exception for study plan related errors"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or self.__class__.__name__
        super().__init__(self.message)


class StudyPlanNotFoundError(BaseStudyPlanException):
    """Raised when a study plan is not found"""
    def __init__(self, plan_id: int):
        super().__init__(
            message=f"Study plan with ID {plan_id} not found",
            code="STUDY_PLAN_NOT_FOUND"
        )
        self.plan_id = plan_id


class UserNotFoundError(BaseStudyPlanException):
    """Raised when a user is not found"""
    def __init__(self, user_id: int):
        super().__init__(
            message=f"User with ID {user_id} not found",
            code="USER_NOT_FOUND"
        )
        self.user_id = user_id


class ValidationError(BaseStudyPlanException):
    """Raised when data validation fails"""
    def __init__(self, message: str, field: str = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR"
        )
        self.field = field


class DatabaseError(BaseStudyPlanException):
    """Raised when database operations fail"""
    def __init__(self, message: str, operation: str = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR"
        )
        self.operation = operation


class DuplicateStudyPlanError(BaseStudyPlanException):
    """Raised when trying to create a duplicate study plan"""
    def __init__(self, message: str = "Study plan already exists"):
        super().__init__(
            message=message,
            code="DUPLICATE_STUDY_PLAN"
        )


class InvalidDateRangeError(ValidationError):
    """Raised when start date is after end date"""
    def __init__(self):
        super().__init__(
            message="Start date must be before end date",
            field="date_range"
        )


class InsufficientPermissionsError(BaseStudyPlanException):
    """Raised when user doesn't have permission for an operation"""
    def __init__(self, user_id: int, operation: str):
        super().__init__(
            message=f"User {user_id} doesn't have permission for operation: {operation}",
            code="INSUFFICIENT_PERMISSIONS"
        )
        self.user_id = user_id
        self.operation = operation