import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime, timedelta
from app.services.ai_services.gemini_service import GeminiService
from app.dtos.ai_study_plan.study_plan import StudyPlanRequest


class TestGeminiService:
    """Gemini API 연동 서비스 테스트"""

    @pytest.fixture
    def sample_request(self):
        """테스트용 학습계획 요청 데이터"""
        return StudyPlanRequest(
            input_data="Python 기초부터 고급까지 3개월 학습계획을 세워주세요",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=90),
            is_challenge=False
        )

    @pytest.fixture
    def expected_ai_response(self):
        """예상되는 AI 응답 데이터"""
        return {
            "title": "Python 3개월 완성 학습계획",
            "total_weeks": 12,
            "difficulty": "beginner_to_advanced",
            "weekly_plans": [
                {
                    "week": 1,
                    "title": "Python 기초 문법",
                    "topics": ["변수와 데이터 타입", "연산자", "조건문"],
                    "goals": ["기본 문법 이해", "간단한 계산기 만들기"],
                    "estimated_hours": 10
                }
            ],
            "milestones": [
                {"week": 4, "milestone": "기초 문법 완료"},
                {"week": 8, "milestone": "중급 개념 완료"},
                {"week": 12, "milestone": "프로젝트 완성"}
            ]
        }

    # 방법 1: genai 모듈 전체를 Mock
    @patch('app.services.ai_services.gemini_service.genai')
    async def test_generate_study_plan_success_v1(self, mock_genai, sample_request, expected_ai_response):
        """학습계획 생성 성공 테스트 - genai 전체 Mock"""
        # Given
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps(expected_ai_response)
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = Mock()  # configure 함수도 Mock

        # GeminiService 생성 (이제 실제 API 호출이 발생하지 않음)
        gemini_service = GeminiService(api_key="test-api-key")

        # When
        result = await gemini_service.generate_study_plan(sample_request)

        # Then
        assert result is not None
        assert result["title"] == "Python 3개월 완성 학습계획"
        assert result["total_weeks"] == 12
        assert len(result["weekly_plans"]) == 1
        assert result["weekly_plans"][0]["week"] == 1

        # API 호출 검증
        mock_model.generate_content_async.assert_called_once()

    # 방법 2: GeminiService 초기화도 Mock
    @patch('app.services.ai_services.gemini_service.genai.configure')
    @patch('app.services.ai_services.gemini_service.genai.GenerativeModel')
    async def test_generate_study_plan_success_v2(self, mock_model_class, mock_configure,
                                                  sample_request, expected_ai_response):
        """학습계획 생성 성공 테스트 - 초기화 포함 Mock"""
        # Given
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps(expected_ai_response)
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_model_class.return_value = mock_model

        # GeminiService 생성
        gemini_service = GeminiService(api_key="test-api-key")

        # When
        result = await gemini_service.generate_study_plan(sample_request)

        # Then
        assert result is not None
        assert result["title"] == "Python 3개월 완성 학습계획"
        mock_configure.assert_called_once_with(api_key="test-api-key")

    # 방법 3: pytest fixture에서 Mock 적용
    @pytest.fixture
    def gemini_service_with_mock(self):
        """Mock이 적용된 GeminiService"""
        with patch('app.services.ai_services.gemini_service.genai.configure') as mock_configure, \
                patch('app.services.ai_services.gemini_service.genai.GenerativeModel') as mock_model_class:
            mock_model = Mock()
            mock_model_class.return_value = mock_model

            service = GeminiService(api_key="test-api-key")
            service._model = mock_model  # 직접 mock 모델 할당

            yield service

    async def test_with_fixture_mock(self, gemini_service_with_mock, sample_request, expected_ai_response):
        """Fixture에서 Mock이 적용된 서비스 테스트"""
        # Given
        mock_response = Mock()
        mock_response.text = json.dumps(expected_ai_response)
        gemini_service_with_mock._model.generate_content_async = AsyncMock(return_value=mock_response)

        # When
        result = await gemini_service_with_mock.generate_study_plan(sample_request)

        # Then
        assert result is not None
        assert result["title"] == "Python 3개월 완성 학습계획"

    # API 에러 테스트 개선
    @patch('app.services.ai_services.gemini_service.genai.configure')
    @patch('app.services.ai_services.gemini_service.genai.GenerativeModel')
    async def test_generate_study_plan_api_error(self, mock_model_class, mock_configure, sample_request):
        """Gemini API 에러 처리 테스트"""
        # Given
        mock_model = Mock()
        mock_model.generate_content_async = AsyncMock(side_effect=Exception("API Rate Limit"))
        mock_model_class.return_value = mock_model

        gemini_service = GeminiService(api_key="test-api-key")

        # When & Then
        with pytest.raises(Exception) as exc_info:
            await gemini_service.generate_study_plan(sample_request)

        assert "API Rate Limit" in str(exc_info.value)

    # 잘못된 JSON 응답 테스트 개선
    @patch('app.services.ai_services.gemini_service.genai.configure')
    @patch('app.services.ai_services.gemini_service.genai.GenerativeModel')
    async def test_generate_study_plan_invalid_json_response(self, mock_model_class, mock_configure, sample_request):
        """잘못된 JSON 응답 처리 테스트"""
        # Given
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Invalid JSON response"
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_model_class.return_value = mock_model

        gemini_service = GeminiService(api_key="test-api-key")

        # When & Then
        with pytest.raises(ValueError) as exc_info:
            await gemini_service.generate_study_plan(sample_request)

        assert "Invalid JSON response from Gemini" in str(exc_info.value)

    # 프롬프트 테스트는 Mock 없이도 가능
    def test_build_prompt_includes_all_requirements(self, sample_request):
        """프롬프트에 모든 요구사항이 포함되는지 테스트"""
        with patch('app.services.ai_services.gemini_service.genai.configure'), \
                patch('app.services.ai_services.gemini_service.genai.GenerativeModel'):
            gemini_service = GeminiService(api_key="test-api-key")

            # When
            prompt = gemini_service._build_prompt(sample_request)

            # Then
            assert "Python 기초부터 고급까지 3개월 학습계획을 세워주세요" in prompt
            assert "JSON 형식" in prompt or "JSON format" in prompt
            assert "weekly_plans" in prompt
            assert "title" in prompt
            assert "goals" in prompt

    def test_build_prompt_challenge_mode(self):
        """챌린지 모드 프롬프트 테스트"""
        with patch('app.services.ai_services.gemini_service.genai.configure'), \
                patch('app.services.ai_services.gemini_service.genai.GenerativeModel'):
            gemini_service = GeminiService(api_key="test-api-key")

            # Given
            challenge_request = StudyPlanRequest(
                input_data="React 2주 집중 챌린지",
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=14),
                is_challenge=True
            )

            # When
            prompt = gemini_service._build_prompt(challenge_request)

            # Then
            assert "챌린지" in prompt or "challenge" in prompt.lower()
            assert "집중" in prompt or "intensive" in prompt.lower()

    def test_validate_ai_response_structure(self, expected_ai_response):
        """AI 응답 구조 검증 테스트"""
        with patch('app.services.ai_services.gemini_service.genai.configure'), \
                patch('app.services.ai_services.gemini_service.genai.GenerativeModel'):
            gemini_service = GeminiService(api_key="test-api-key")

            # When & Then
            # 올바른 구조는 예외 없이 통과
            gemini_service._validate_response_structure(expected_ai_response)

            # 필수 필드 누락 시 예외 발생
            invalid_response = {"title": "Test"}
            with pytest.raises(ValueError) as exc_info:
                gemini_service._validate_response_structure(invalid_response)

            assert "Missing required fields" in str(exc_info.value)

    @patch('app.services.ai_services.gemini_service.genai.configure')
    @patch('app.services.ai_services.gemini_service.genai.GenerativeModel')
    async def test_generate_study_plan_different_durations(self, mock_model_class, mock_configure,
                                                           expected_ai_response):
        """다양한 학습 기간에 대한 테스트"""
        # Given
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps(expected_ai_response)
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_model_class.return_value = mock_model

        gemini_service = GeminiService(api_key="test-api-key")

        test_cases = [
            (7, "1주"),  # 1주 단기
            (30, "1개월"),  # 1개월 중기
            (180, "6개월"),  # 6개월 장기
        ]

        for days, period_name in test_cases:
            # Given
            request = StudyPlanRequest(
                input_data=f"JavaScript {period_name} 학습계획",
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=days),
                is_challenge=False
            )

            # When
            result = await gemini_service.generate_study_plan(request)

            # Then
            assert result is not None
            assert "title" in result