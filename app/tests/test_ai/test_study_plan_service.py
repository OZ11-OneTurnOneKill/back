import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from app.services.ai_services.study_plan_service import StudyPlanService
from app.services.ai_services.gemini_service import GeminiService
from app.dtos.ai_study_plan.study_plan import StudyPlanRequest, StudyPlanResponse
from app.models.ai import StudyPlan


class TestStudyPlanService:
    """학습계획 생성 서비스 테스트"""

    @pytest.fixture
    def mock_gemini_service(self):
        """Mock Gemini 서비스"""
        service = Mock(spec=GeminiService)
        service.generate_study_plan = AsyncMock()
        return service

    @pytest.fixture
    def study_plan_service(self, mock_gemini_service):
        """StudyPlanService 인스턴스"""
        return StudyPlanService(gemini_service=mock_gemini_service)

    @pytest.fixture
    def sample_request(self):
        """테스트용 학습계획 요청"""
        return StudyPlanRequest(
            input_data="Python 웹 개발 3개월 과정",
            start_date=datetime(2025, 8, 15, 9, 0, 0),
            end_date=datetime(2025, 11, 15, 18, 0, 0),
            is_challenge=False
        )

    @pytest.fixture
    def sample_ai_response(self):
        """테스트용 AI 응답"""
        return {
            "title": "Python 웹 개발 완성 과정",
            "total_weeks": 12,
            "difficulty": "beginner_to_intermediate",
            "weekly_plans": [
                {
                    "week": 1,
                    "title": "Python 기초",
                    "topics": ["문법", "데이터 타입"],
                    "goals": ["기초 문법 이해"],
                    "estimated_hours": 8
                }
            ],
            "milestones": [
                {"week": 4, "milestone": "기초 완료"}
            ]
        }

    @pytest.fixture
    def sample_study_plan_model(self):
        """테스트용 StudyPlan 모델 인스턴스"""
        return StudyPlan(
            id=1,
            user_id=123,
            input_data="Python 웹 개발 3개월 과정",
            output_data='{"title": "Python 웹 개발 완성 과정", "total_weeks": 12}',
            is_challenge=False,
            start_date=datetime(2025, 8, 15, 9, 0, 0),
            end_date=datetime(2025, 11, 15, 18, 0, 0),
            created_at=datetime(2025, 8, 11, 10, 0, 0)
        )

    @patch('app.models.ai.StudyPlan.create')  # ✅ 올바른 import 경로
    async def test_create_study_plan_success(
            self,
            mock_create,
            study_plan_service,
            sample_request,
            sample_ai_response,
            sample_study_plan_model
    ):
        """학습계획 생성 성공 테스트"""
        # Given
        user_id = 123
        study_plan_service.gemini_service.generate_study_plan.return_value = sample_ai_response
        mock_create.return_value = sample_study_plan_model  # ✅ 동기 메서드

        # When
        result = await study_plan_service.create_study_plan(
            user_id=user_id,
            request=sample_request
        )

        # Then
        assert isinstance(result, StudyPlanResponse)
        assert result.user_id == user_id
        assert result.input_data == sample_request.input_data
        assert "Python 웹 개발 완성 과정" in result.output_data
        assert result.is_challenge == False

        # 서비스 호출 검증
        study_plan_service.gemini_service.generate_study_plan.assert_called_once_with(sample_request)

        # DB 저장 검증
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs['user_id'] == user_id
        assert call_kwargs['input_data'] == sample_request.input_data
        assert call_kwargs['is_challenge'] == sample_request.is_challenge

    async def test_create_study_plan_gemini_api_failure(
            self,
            study_plan_service,
            sample_request
    ):
        """Gemini API 실패 시 테스트"""
        # Given
        user_id = 123
        study_plan_service.gemini_service.generate_study_plan.side_effect = Exception("API Error")

        # When & Then
        with pytest.raises(Exception) as exc_info:
            await study_plan_service.create_study_plan(
                user_id=user_id,
                request=sample_request
            )

        assert "API Error" in str(exc_info.value)

    @patch('app.models.ai.StudyPlan.get_or_none')  # ✅ 올바른 import 경로
    async def test_get_study_plan_by_id_success(
            self,
            mock_get_or_none,
            study_plan_service,
            sample_study_plan_model
    ):
        """ID로 학습계획 조회 성공 테스트"""
        # Given
        study_plan_id = 1
        user_id = 123
        mock_get_or_none.return_value = sample_study_plan_model  # ✅ 동기 메서드

        # When
        result = await study_plan_service.get_study_plan_by_id(
            study_plan_id=study_plan_id,
            user_id=user_id
        )

        # Then
        assert isinstance(result, StudyPlanResponse)
        assert result.id == study_plan_id
        assert result.user_id == user_id

        mock_get_or_none.assert_called_once_with(id=study_plan_id)

    @patch('app.models.ai.StudyPlan.get_or_none')
    async def test_get_study_plan_by_id_not_found(
            self,
            mock_get_or_none,
            study_plan_service
    ):
        """존재하지 않는 학습계획 조회 테스트"""
        # Given
        study_plan_id = 999
        user_id = 123
        mock_get_or_none.return_value = None  # ✅ 동기 메서드

        # When & Then
        with pytest.raises(ValueError) as exc_info:
            await study_plan_service.get_study_plan_by_id(
                study_plan_id=study_plan_id,
                user_id=user_id
            )

        assert "Study plan not found" in str(exc_info.value)

    @patch('app.models.ai.StudyPlan.get_or_none')
    async def test_get_study_plan_by_id_wrong_user(
            self,
            mock_get_or_none,
            study_plan_service
    ):
        """다른 사용자의 학습계획 조회 시도 테스트"""
        # Given
        study_plan_id = 1
        user_id = 123
        other_user_id = 456

        # 다른 사용자의 학습계획
        other_user_plan = StudyPlan(
            id=study_plan_id,
            user_id=other_user_id,  # 다른 사용자
            input_data="테스트 입력",
            output_data='{"title": "테스트 계획"}',
            is_challenge=False,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            created_at=datetime.now()
        )

        mock_get_or_none.return_value = other_user_plan

        # When & Then
        with pytest.raises(ValueError) as exc_info:
            await study_plan_service.get_study_plan_by_id(
                study_plan_id=study_plan_id,
                user_id=user_id
            )

        assert "Access denied" in str(exc_info.value)

    @patch('app.models.ai.StudyPlan.filter')  # ✅ 올바른 import 경로
    async def test_get_user_study_plans_success(
            self,
            mock_filter,
            study_plan_service,
            sample_study_plan_model
    ):
        """사용자 학습계획 목록 조회 성공 테스트"""
        # Given
        user_id = 123

        # ✅ Mock QuerySet 체인을 올바르게 설정
        mock_queryset = Mock()
        mock_queryset.order_by = Mock(return_value=mock_queryset)
        mock_queryset.limit = Mock(return_value=mock_queryset)
        mock_queryset.offset = Mock(return_value=[sample_study_plan_model])  # ✅ 최종 결과는 list
        mock_filter.return_value = mock_queryset

        # When
        result = await study_plan_service.get_user_study_plans(
            user_id=user_id,
            limit=10,
            offset=0
        )

        # Then
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], StudyPlanResponse)
        assert result[0].user_id == user_id

        # QuerySet 호출 검증
        mock_filter.assert_called_once_with(user_id=user_id)
        mock_queryset.order_by.assert_called_once_with("-created_at")
        mock_queryset.limit.assert_called_once_with(10)
        mock_queryset.offset.assert_called_once_with(0)

    @patch('app.models.ai.StudyPlan.get_or_none')
    async def test_update_study_plan_success(
            self,
            mock_get_or_none,
            study_plan_service,
            sample_ai_response,
            sample_study_plan_model
    ):
        """학습계획 업데이트 성공 테스트"""
        # Given
        study_plan_id = 1
        user_id = 123
        update_data = {
            "input_data": "수정된 Python 웹 개발 과정",
            "start_date": datetime(2025, 9, 1, 9, 0, 0)
        }

        # Mock StudyPlan 인스턴스
        mock_plan_instance = Mock(spec=StudyPlan)
        mock_plan_instance.id = study_plan_id
        mock_plan_instance.user_id = user_id
        mock_plan_instance.input_data = "기존 입력"
        mock_plan_instance.output_data = '{"title": "기존 계획"}'
        mock_plan_instance.is_challenge = False
        mock_plan_instance.start_date = datetime(2025, 8, 15, 9, 0, 0)
        mock_plan_instance.end_date = datetime(2025, 11, 15, 18, 0, 0)
        mock_plan_instance.created_at = datetime.now()

        # ✅ update_from_dict는 동기, save는 비동기
        mock_plan_instance.update_from_dict = Mock(return_value=mock_plan_instance)
        mock_plan_instance.save = AsyncMock()

        mock_get_or_none.return_value = mock_plan_instance
        study_plan_service.gemini_service.generate_study_plan.return_value = sample_ai_response

        # ✅ 올바른 경로로 StudyPlan.get Mock
        with patch('app.models.ai.StudyPlan.get') as mock_get:
            # 업데이트된 인스턴스 반환
            updated_instance = Mock(spec=StudyPlan)
            updated_instance.id = study_plan_id
            updated_instance.user_id = user_id
            updated_instance.input_data = "수정된 Python 웹 개발 과정"
            updated_instance.output_data = '{"title": "수정된 계획"}'
            updated_instance.is_challenge = False
            updated_instance.start_date = datetime(2025, 9, 1, 9, 0, 0)
            updated_instance.end_date = datetime(2025, 11, 15, 18, 0, 0)
            updated_instance.created_at = datetime.now()

            mock_get.return_value = updated_instance  # ✅ 동기 메서드

            # When
            result = await study_plan_service.update_study_plan(
                study_plan_id=study_plan_id,
                user_id=user_id,
                update_data=update_data
            )

            # Then
            assert isinstance(result, StudyPlanResponse)
            assert result.input_data == "수정된 Python 웹 개발 과정"

            # 메서드 호출 검증
            mock_plan_instance.update_from_dict.assert_called_once_with(update_data)
            mock_plan_instance.save.assert_called_once()
            mock_get.assert_called_once_with(id=study_plan_id)

    @patch('app.models.ai.StudyPlan.get_or_none')
    async def test_update_study_plan_with_input_data_change(
            self,
            mock_get_or_none,
            study_plan_service,
            sample_ai_response,
            sample_study_plan_model
    ):
        """입력 데이터 변경 시 AI 재생성 테스트"""
        # Given
        study_plan_id = 1
        user_id = 123
        update_data = {
            "input_data": "완전히 새로운 학습계획"
        }

        mock_plan_instance = Mock(spec=StudyPlan)
        mock_plan_instance.id = study_plan_id
        mock_plan_instance.user_id = user_id
        mock_plan_instance.input_data = "기존 입력"
        mock_plan_instance.is_challenge = False
        mock_plan_instance.start_date = datetime(2025, 8, 15, 9, 0, 0)
        mock_plan_instance.end_date = datetime(2025, 11, 15, 18, 0, 0)
        mock_plan_instance.update_from_dict = Mock(return_value=mock_plan_instance)
        mock_plan_instance.save = AsyncMock()

        mock_get_or_none.return_value = mock_plan_instance
        study_plan_service.gemini_service.generate_study_plan.return_value = sample_ai_response

        # ✅ 올바른 경로 사용
        with patch('app.models.ai.StudyPlan.get') as mock_get:
            mock_get.return_value = mock_plan_instance

            # When
            await study_plan_service.update_study_plan(
                study_plan_id=study_plan_id,
                user_id=user_id,
                update_data=update_data
            )

            # Then - AI 재생성이 호출되었는지 확인
            study_plan_service.gemini_service.generate_study_plan.assert_called_once()

            # 호출된 request 확인
            call_args = study_plan_service.gemini_service.generate_study_plan.call_args[0][0]
            assert call_args.input_data == "완전히 새로운 학습계획"

    @patch('app.models.ai.StudyPlan.get_or_none')
    async def test_delete_study_plan_success(
            self,
            mock_get_or_none,
            study_plan_service,
            sample_study_plan_model
    ):
        """학습계획 삭제 성공 테스트"""
        # Given
        study_plan_id = 1
        user_id = 123

        mock_plan_instance = Mock(spec=StudyPlan)
        mock_plan_instance.id = study_plan_id
        mock_plan_instance.user_id = user_id
        mock_plan_instance.delete = AsyncMock()  # ✅ 비동기 메서드

        mock_get_or_none.return_value = mock_plan_instance

        # When
        await study_plan_service.delete_study_plan(
            study_plan_id=study_plan_id,
            user_id=user_id
        )

        # Then
        mock_plan_instance.delete.assert_called_once()

    @patch('app.models.ai.StudyPlan.get_or_none')
    async def test_delete_study_plan_not_found(
            self,
            mock_get_or_none,
            study_plan_service
    ):
        """존재하지 않는 학습계획 삭제 시도 테스트"""
        # Given
        study_plan_id = 999
        user_id = 123
        mock_get_or_none.return_value = None  # ✅ 동기 메서드

        # When & Then
        with pytest.raises(ValueError) as exc_info:
            await study_plan_service.delete_study_plan(
                study_plan_id=study_plan_id,
                user_id=user_id
            )

        assert "Study plan not found" in str(exc_info.value)

    @patch('app.models.ai.StudyPlan.get_or_none')
    async def test_delete_study_plan_access_denied(
            self,
            mock_get_or_none,
            study_plan_service
    ):
        """권한 없는 학습계획 삭제 시도 테스트"""
        # Given
        study_plan_id = 1
        user_id = 123
        other_user_id = 456

        mock_plan_instance = Mock(spec=StudyPlan)
        mock_plan_instance.id = study_plan_id
        mock_plan_instance.user_id = other_user_id  # 다른 사용자

        mock_get_or_none.return_value = mock_plan_instance

        # When & Then
        with pytest.raises(ValueError) as exc_info:
            await study_plan_service.delete_study_plan(
                study_plan_id=study_plan_id,
                user_id=user_id
            )

        assert "Access denied" in str(exc_info.value)

    @patch('app.services.ai_services.study_plan_service.logger')
    @patch('app.models.ai.StudyPlan.create')  # ✅ 올바른 import 경로
    async def test_create_study_plan_logs_creation(
            self,
            mock_create,
            mock_logger,
            study_plan_service,
            sample_request,
            sample_ai_response,
            sample_study_plan_model
    ):
        """학습계획 생성 시 로깅 테스트"""
        # Given
        user_id = 123
        study_plan_service.gemini_service.generate_study_plan.return_value = sample_ai_response
        mock_create.return_value = sample_study_plan_model

        # When
        await study_plan_service.create_study_plan(
            user_id=user_id,
            request=sample_request
        )

        # Then
        mock_logger.info.assert_called()
        log_call_args = str(mock_logger.info.call_args_list)
        assert "Creating study plan for user" in log_call_args

    @patch('app.models.ai.StudyPlan.filter')  # ✅ 올바른 import 경로
    async def test_get_user_study_plans_with_pagination(
            self,
            mock_filter,
            study_plan_service
    ):
        """페이지네이션이 있는 학습계획 목록 조회 테스트"""
        # Given
        user_id = 123
        limit = 5
        offset = 10

        # ✅ Mock QuerySet 체인을 올바르게 설정
        mock_queryset = Mock()
        mock_queryset.order_by = Mock(return_value=mock_queryset)
        mock_queryset.limit = Mock(return_value=mock_queryset)
        mock_queryset.offset = Mock(return_value=[])  # ✅ 빈 list 반환
        mock_filter.return_value = mock_queryset

        # When
        result = await study_plan_service.get_user_study_plans(
            user_id=user_id,
            limit=limit,
            offset=offset
        )

        # Then
        assert isinstance(result, list)
        assert len(result) == 0
        mock_filter.assert_called_once_with(user_id=user_id)
        mock_queryset.limit.assert_called_once_with(limit)
        mock_queryset.offset.assert_called_once_with(offset)

    # ✅ 추가: 에러 케이스 테스트
    @patch('app.models.ai.StudyPlan.create')
    async def test_create_study_plan_database_error(
            self,
            mock_create,
            study_plan_service,
            sample_request,
            sample_ai_response
    ):
        """데이터베이스 에러 시 테스트"""
        # Given
        user_id = 123
        study_plan_service.gemini_service.generate_study_plan.return_value = sample_ai_response
        mock_create.side_effect = Exception("Database connection failed")

        # When & Then
        with pytest.raises(Exception) as exc_info:
            await study_plan_service.create_study_plan(
                user_id=user_id,
                request=sample_request
            )

        assert "Database connection failed" in str(exc_info.value)

    # ✅ 추가: 경계값 테스트
    @patch('app.models.ai.StudyPlan.filter')
    async def test_get_user_study_plans_edge_cases(
            self,
            mock_filter,
            study_plan_service
    ):
        """경계값 테스트 (limit=0, offset=0 등)"""
        # Given
        user_id = 123

        mock_queryset = Mock()
        mock_queryset.order_by = Mock(return_value=mock_queryset)
        mock_queryset.limit = Mock(return_value=mock_queryset)
        mock_queryset.offset = Mock(return_value=[])
        mock_filter.return_value = mock_queryset

        # When - limit=0인 경우
        result = await study_plan_service.get_user_study_plans(
            user_id=user_id,
            limit=0,
            offset=0
        )

        # Then
        assert isinstance(result, list)
        mock_queryset.limit.assert_called_with(0)
        mock_queryset.offset.assert_called_with(0)