import pytest
from datetime import datetime
from pydantic import ValidationError
from app.dtos.ai.study_plan import StudyPlanRequest, StudyPlanResponse


class TestStudyPlanRequest:
    """학습계획 요청 데이터 검증 테스트"""

    def test_valid_study_plan_request(self):
        """올바른 학습계획 요청 데이터 검증"""
        # Given
        valid_data = {
            "input_data": "Python 기초부터 고급까지 3개월 학습계획을 세워주세요",
            "start_date": "2025-08-15T09:00:00",
            "end_date": "2025-11-15T18:00:00",
            "is_challenge": False
        }

        # When & Then
        request = StudyPlanRequest(**valid_data)
        assert request.input_data == "Python 기초부터 고급까지 3개월 학습계획을 세워주세요"
        assert request.is_challenge == False
        assert isinstance(request.start_date, datetime)
        assert isinstance(request.end_date, datetime)

    def test_missing_required_fields(self):
        """필수 필드 누락 시 검증 실패"""
        # Given
        invalid_data = {
            "is_challenge": True
            # input_data, start_date, end_date 누락
        }

        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            StudyPlanRequest(**invalid_data)

        errors = exc_info.value.errors()
        missing_fields = [error["loc"][0] for error in errors]
        assert "input_data" in missing_fields
        assert "start_date" in missing_fields
        assert "end_date" in missing_fields

    def test_empty_input_data(self):
        """빈 입력 데이터 검증 실패"""
        # Given
        invalid_data = {
            "input_data": "",
            "start_date": "2025-08-15T09:00:00",
            "end_date": "2025-11-15T18:00:00"
        }

        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            StudyPlanRequest(**invalid_data)

        error = exc_info.value.errors()[0]
        assert error["loc"] == ("input_data",)
        assert "at least 1 character" in error["msg"]

    def test_invalid_date_format(self):
        """잘못된 날짜 형식 검증 실패"""
        # Given
        invalid_data = {
            "input_data": "테스트 학습계획",
            "start_date": "2025-13-45",  # 잘못된 날짜
            "end_date": "2025-11-15T18:00:00"
        }

        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            StudyPlanRequest(**invalid_data)

        error = exc_info.value.errors()[0]
        assert error["loc"] == ("start_date",)

    def test_end_date_before_start_date(self):
        """종료일이 시작일보다 이른 경우 검증 실패"""
        # Given
        invalid_data = {
            "input_data": "테스트 학습계획",
            "start_date": "2025-11-15T09:00:00",
            "end_date": "2025-08-15T18:00:00"  # 시작일보다 이른 종료일
        }

        # When & Then
        with pytest.raises(ValidationError) as exc_info:
            StudyPlanRequest(**invalid_data)

        # 커스텀 검증 메시지 확인
        error = exc_info.value.errors()[0]
        assert "end_date must be after start_date" in error["msg"]

    def test_default_is_challenge_false(self):
        """is_challenge 기본값이 False인지 확인"""
        # Given
        data_without_challenge = {
            "input_data": "Python 학습계획",
            "start_date": "2025-08-15T09:00:00",
            "end_date": "2025-11-15T18:00:00"
        }

        # When
        request = StudyPlanRequest(**data_without_challenge)

        # Then
        assert request.is_challenge == False


class TestStudyPlanResponse:
    """학습계획 응답 데이터 검증 테스트"""

    def test_valid_study_plan_response(self):
        """올바른 학습계획 응답 데이터 검증"""
        # Given
        valid_response_data = {
            "id": 1,
            "user_id": 123,
            "input_data": "Python 학습계획 요청",
            "output_data": "{'weeks': [{'week': 1, 'topics': ['기초문법']}]}",
            "is_challenge": False,
            "start_date": "2025-08-15T09:00:00",
            "end_date": "2025-11-15T18:00:00",
            "created_at": "2025-08-11T10:00:00"
        }

        # When & Then
        response = StudyPlanResponse(**valid_response_data)
        assert response.id == 1
        assert response.user_id == 123
        assert response.output_data is not None
        assert isinstance(response.created_at, datetime)