import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError
from app.dtos.ai_study_plan.ai_study_plan_request import AIStudyPlanCreateRequest, AIStudyPlanUpdateRequest
from app.dtos.ai_study_plan.ai_study_plan_response import AIStudyPlanResponse, StudyPlanStatus


class TestAIStudyPlanSchemas:
    """AI 스터디 플랜 Pydantic 스키마 테스트"""
    
    def test_create_request_valid_data(self):
        """유효한 데이터로 생성 요청 스키마 테스트"""
        valid_data = {
            "user_id": 1,
            "is_challenge": False,
            "input_data": "I want to learn Python web development",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=30)
        }
        
        request = AIStudyPlanCreateRequest(**valid_data)
        
        assert request.user_id == 1
        assert request.is_challenge == False
        assert request.input_data == "I want to learn Python web development"
        assert isinstance(request.start_date, datetime)
        assert isinstance(request.end_date, datetime)
    
    def test_create_request_default_challenge(self):
        """is_challenge 기본값 테스트"""
        data = {
            "user_id": 1,
            "input_data": "Test input",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=30)
        }
        
        request = AIStudyPlanCreateRequest(**data)
        assert request.is_challenge == False  # 기본값
    
    def test_create_request_challenge_mode(self):
        """챌린지 모드 생성 요청 테스트"""
        data = {
            "user_id": 2,
            "is_challenge": True,
            "input_data": "30-day coding challenge",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=30)
        }
        
        request = AIStudyPlanCreateRequest(**data)
        assert request.is_challenge == True
    
    def test_create_request_missing_required_fields(self):
        """필수 필드 누락 시 유효성 검사 실패 테스트"""
        incomplete_data = {
            "user_id": 1,
            "input_data": "Test input"
            # start_date, end_date 누락
        }
        
        with pytest.raises(ValidationError) as exc_info:
            AIStudyPlanCreateRequest(**incomplete_data)
        
        errors = exc_info.value.errors()
        required_fields = {error['loc'][0] for error in errors}
        assert 'start_date' in required_fields
        assert 'end_date' in required_fields
    
    def test_create_request_invalid_user_id(self):
        """잘못된 user_id 타입 테스트"""
        data = {
            "user_id": "invalid",  # 문자열은 정수로 변환되거나 에러
            "input_data": "Test input",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=30)
        }
        
        # Pydantic은 문자열을 정수로 변환 시도하므로, 변환 불가능한 문자열 사용
        data["user_id"] = "not_a_number"
        
        with pytest.raises(ValidationError) as exc_info:
            AIStudyPlanCreateRequest(**data)
        
        errors = exc_info.value.errors()
        assert any(error['loc'][0] == 'user_id' for error in errors)
    
    def test_create_request_invalid_dates(self):
        """잘못된 날짜 타입 테스트"""
        data = {
            "user_id": 1,
            "input_data": "Test input",
            "start_date": "invalid_date",
            "end_date": datetime.now() + timedelta(days=30)
        }
        
        with pytest.raises(ValidationError) as exc_info:
            AIStudyPlanCreateRequest(**data)
        
        errors = exc_info.value.errors()
        assert any(error['loc'][0] == 'start_date' for error in errors)
    
    def test_update_request_all_optional(self):
        """업데이트 요청의 모든 필드가 선택사항임을 테스트"""
        update = AIStudyPlanUpdateRequest()
        
        assert update.input_data is None
        assert update.start_date is None
        assert update.end_date is None
        assert update.is_challenge is None
        assert update.status is None
    
    def test_update_request_partial_data(self):
        """부분 업데이트 요청 테스트"""
        data = {
            "input_data": "Updated learning goal",
            "is_challenge": True
        }
        
        update = AIStudyPlanUpdateRequest(**data)
        
        assert update.input_data == "Updated learning goal"
        assert update.is_challenge == True
        assert update.start_date is None
        assert update.end_date is None
        assert update.status is None
    
    def test_update_request_with_dates(self):
        """날짜 포함 업데이트 요청 테스트"""
        new_start = datetime.now()
        new_end = datetime.now() + timedelta(days=45)
        
        data = {
            "start_date": new_start,
            "end_date": new_end,
            "status": StudyPlanStatus.ACTIVE
        }
        
        update = AIStudyPlanUpdateRequest(**data)
        
        assert update.start_date == new_start
        assert update.end_date == new_end
        assert update.status == StudyPlanStatus.ACTIVE
        assert update.input_data is None
        assert update.is_challenge is None
    
    def test_update_request_with_status(self):
        """상태 업데이트 요청 테스트"""
        data = {
            "status": StudyPlanStatus.COMPLETED
        }
        
        update = AIStudyPlanUpdateRequest(**data)
        
        assert update.status == StudyPlanStatus.COMPLETED
        assert update.input_data is None
        assert update.start_date is None
    
    def test_response_schema_valid(self):
        """유효한 응답 스키마 테스트"""
        data = {
            "id": 1,
            "user_id": 1,
            "is_challenge": False,
            "input_data": "Test input",
            "output_data": "Test output",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=30),
            "status": StudyPlanStatus.PLANNED,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "is_active": False,
            "progress_percentage": 10,
            "days_remaining": 25
        }
        
        response = AIStudyPlanResponse(**data)
        
        assert response.id == 1
        assert response.user_id == 1
        assert response.is_challenge == False
        assert response.status == StudyPlanStatus.PLANNED
        assert isinstance(response.created_at, datetime)
        assert isinstance(response.updated_at, datetime)
        assert response.is_active == False
        assert response.progress_percentage == 10
        assert response.days_remaining == 25
    
    def test_response_schema_missing_fields(self):
        """응답 스키마 필수 필드 누락 테스트"""
        incomplete_data = {
            "id": 1,
            "user_id": 1
            # 다른 필수 필드들 누락
        }
        
        with pytest.raises(ValidationError) as exc_info:
            AIStudyPlanResponse(**incomplete_data)
        
        errors = exc_info.value.errors()
        required_fields = {error['loc'][0] for error in errors}
        
        expected_fields = {
            'input_data', 'output_data', 'start_date', 
            'end_date', 'created_at', 'updated_at'
        }
        
        assert expected_fields.issubset(required_fields)
    
    def test_response_schema_optional_fields(self):
        """응답 스키마 선택사항 필드 테스트"""
        base_data = {
            "id": 1,
            "user_id": 1,
            "is_challenge": False,
            "input_data": "Test input",
            "output_data": "Test output",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=30),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        response = AIStudyPlanResponse(**base_data)
        
        # 선택사항 필드들의 기본값 확인
        assert response.status == StudyPlanStatus.PLANNED  # 기본값
        assert response.is_active == False  # 기본값
        assert response.progress_percentage is None  # 기본값
        assert response.days_remaining is None  # 기본값
    
    def test_study_plan_status_enum(self):
        """StudyPlanStatus Enum 테스트"""
        # 모든 유효한 상태값 테스트
        valid_statuses = [
            StudyPlanStatus.PLANNED,
            StudyPlanStatus.ACTIVE,
            StudyPlanStatus.COMPLETED,
            StudyPlanStatus.PAUSED,
            StudyPlanStatus.CANCELLED
        ]
        
        for status in valid_statuses:
            assert isinstance(status, StudyPlanStatus)
            assert isinstance(status.value, str)
        
        # 문자열 값 확인
        assert StudyPlanStatus.PLANNED.value == "planned"
        assert StudyPlanStatus.ACTIVE.value == "active"
        assert StudyPlanStatus.COMPLETED.value == "completed"
        assert StudyPlanStatus.PAUSED.value == "paused"
        assert StudyPlanStatus.CANCELLED.value == "cancelled"
    
    def test_model_serialization(self):
        """모델 직렬화 테스트"""
        data = {
            "user_id": 1,
            "is_challenge": True,
            "input_data": "Test serialization",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=30)
        }
        
        request = AIStudyPlanCreateRequest(**data)
        serialized = request.model_dump()
        
        assert isinstance(serialized, dict)
        assert serialized["user_id"] == 1
        assert serialized["is_challenge"] == True
        assert serialized["input_data"] == "Test serialization"
        assert isinstance(serialized["start_date"], datetime)
        assert isinstance(serialized["end_date"], datetime)
    
    def test_model_dump_exclude_unset(self):
        """설정되지 않은 필드 제외 직렬화 테스트"""
        update = AIStudyPlanUpdateRequest(
            input_data="Updated input",
            is_challenge=True
        )
        
        dumped = update.model_dump(exclude_unset=True)
        
        assert "input_data" in dumped
        assert "is_challenge" in dumped
        assert "start_date" not in dumped
        assert "end_date" not in dumped
        assert "status" not in dumped
    
    def test_json_serialization(self):
        """JSON 직렬화 테스트"""
        data = {
            "user_id": 1,
            "is_challenge": False,
            "input_data": "JSON test",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=30)
        }
        
        request = AIStudyPlanCreateRequest(**data)
        json_str = request.model_dump_json()
        
        assert isinstance(json_str, str)
        assert '"user_id":1' in json_str or '"user_id": 1' in json_str
        assert '"is_challenge":false' in json_str or '"is_challenge": false' in json_str
    
    def test_response_with_computed_fields(self):
        """계산된 필드가 포함된 응답 테스트"""
        now = datetime.now()
        data = {
            "id": 1,
            "user_id": 1,
            "is_challenge": True,
            "input_data": "Active plan",
            "output_data": "Active plan output",
            "start_date": now - timedelta(days=10),  # 10일 전 시작
            "end_date": now + timedelta(days=20),    # 20일 후 종료
            "status": StudyPlanStatus.ACTIVE,
            "created_at": now - timedelta(days=15),
            "updated_at": now,
            "is_active": True,
            "progress_percentage": 33,
            "days_remaining": 20
        }
        
        response = AIStudyPlanResponse(**data)
        
        assert response.is_active == True
        assert response.progress_percentage == 33
        assert response.days_remaining == 20
        assert response.status == StudyPlanStatus.ACTIVE
    
    def test_progress_percentage_validation(self):
        """진행률 범위 검증 테스트"""
        base_data = {
            "id": 1,
            "user_id": 1,
            "is_challenge": False,
            "input_data": "Test",
            "output_data": "Test output",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=30),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # 유효한 진행률 (0-100)
        for progress in [0, 50, 100]:
            data = {**base_data, "progress_percentage": progress}
            response = AIStudyPlanResponse(**data)
            assert response.progress_percentage == progress
        
        # 유효하지 않은 진행률
        for invalid_progress in [-10, 150]:
            data = {**base_data, "progress_percentage": invalid_progress}
            with pytest.raises(ValidationError):
                AIStudyPlanResponse(**data)