import pytest
import json
from unittest.mock import Mock, patch, AsyncMock

from app.services.ai_services.gemini_service import GeminiService


class TestGeminiServiceSummary:
    """Gemini 서비스의 요약 기능 테스트

    이 클래스는 AI API 연동 부분의 안정성을 검증합니다.
    외부 API의 다양한 응답 시나리오를 시뮬레이션하여 견고한 시스템을 만듭니다.
    """

    @pytest.fixture
    def sample_content(self):
        """테스트용 요약할 내용"""
        return """
        인공지능(AI)은 컴퓨터 시스템이 인간과 같은 지능적 행동을 수행할 수 있게 하는 기술입니다.
        머신러닝은 AI의 하위 분야로, 데이터에서 패턴을 학습하여 예측을 수행합니다.
        딥러닝은 신경망을 사용하는 머신러닝의 특별한 형태입니다.
        자연어 처리는 컴퓨터가 인간의 언어를 이해하고 생성하는 기술입니다.
        """

    @pytest.fixture
    def expected_summary_response(self):
        """예상되는 AI 요약 응답"""
        return {
            "title": "AI 기초 개념 정리",
            "summary_type": "general",
            "summary": "인공지능은 컴퓨터가 인간같은 지능을 구현하는 기술입니다. 주요 분야로는 머신러닝, 딥러닝, 자연어 처리가 있습니다.",
            "key_points": [
                "AI는 인간같은 지능적 행동을 구현하는 기술",
                "머신러닝은 데이터에서 패턴을 학습",
                "딥러닝은 신경망 기반 머신러닝",
                "자연어 처리는 인간 언어 이해 기술"
            ],
            "word_count": 120,
            "summary_ratio": "25%"
        }

    @patch('app.services.ai_services.gemini_service.genai.configure')
    @patch('app.services.ai_services.gemini_service.genai.GenerativeModel')
    async def test_generate_summary_success(
            self,
            mock_model_class,
            mock_configure,
            sample_content,
            expected_summary_response
    ):
        """요약 생성 성공 테스트

        AI 서비스가 정상적으로 요약을 생성하는 경우를 테스트합니다.
        """
        # Given: 성공적인 AI 응답 설정
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps(expected_summary_response)
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_model_class.return_value = mock_model

        gemini_service = GeminiService(api_key="test-api-key")

        # When: 요약 생성 실행
        result = await gemini_service.generate_summary(
            content=sample_content,
            summary_type="general",
            title="AI 기초 개념 정리"
        )

        # Then: 결과 검증
        assert result is not None
        assert result["title"] == "AI 기초 개념 정리"
        assert result["summary_type"] == "general"
        assert "인공지능" in result["summary"]
        assert len(result["key_points"]) == 4

        # API 호출이 올바르게 이루어졌는지 확인
        mock_model.generate_content_async.assert_called_once()

    @patch('app.services.ai_services.gemini_service.genai.configure')
    @patch('app.services.ai_services.gemini_service.genai.GenerativeModel')
    async def test_generate_summary_with_markdown_response(
            self,
            mock_model_class,
            mock_configure,
            sample_content,
            expected_summary_response
    ):
        """마크다운 코드 블록이 포함된 응답 처리 테스트

        AI가 JSON을 마크다운 코드 블록으로 감싸서 반환할 때의 처리를 확인합니다.
        """
        # Given: 마크다운으로 감싸진 JSON 응답
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = f"```json\n{json.dumps(expected_summary_response)}\n```"
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_model_class.return_value = mock_model

        gemini_service = GeminiService(api_key="test-api-key")

        # When: 요약 생성 실행
        result = await gemini_service.generate_summary(
            content=sample_content,
            summary_type="general",
            title="AI 기초 개념 정리"
        )

        # Then: 정상적으로 파싱되어야 함
        assert result["title"] == "AI 기초 개념 정리"
        assert "key_points" in result

    @patch('app.services.ai_services.gemini_service.genai.configure')
    @patch('app.services.ai_services.gemini_service.genai.GenerativeModel')
    async def test_generate_summary_invalid_json_fallback(
            self,
            mock_model_class,
            mock_configure,
            sample_content
    ):
        """잘못된 JSON 응답 시 폴백 처리 테스트

        AI가 올바르지 않은 JSON을 반환했을 때 안전한 폴백 응답을 제공하는지 확인합니다.
        """
        # Given: 잘못된 JSON 응답
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "잘못된 JSON 형식의 응답입니다."
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_model_class.return_value = mock_model

        gemini_service = GeminiService(api_key="test-api-key")

        # When: 요약 생성 실행
        result = await gemini_service.generate_summary(
            content=sample_content,
            summary_type="general",
            title="테스트 제목"
        )

        # Then: 폴백 응답이 반환되어야 함
        assert result is not None
        assert "_fallback" in result  # 폴백 응답임을 나타내는 플래그
        assert "테스트 제목" in result["title"]
        assert result["summary_type"] == "general"

    @patch('app.services.ai_services.gemini_service.genai.configure')
    @patch('app.services.ai_services.gemini_service.genai.GenerativeModel')
    async def test_generate_summary_api_error(
            self,
            mock_model_class,
            mock_configure,
            sample_content
    ):
        """API 호출 실패 시 예외 처리 테스트"""
        # Given: API 호출 실패 설정
        mock_model = Mock()
        mock_model.generate_content_async = AsyncMock(
            side_effect=Exception("API Rate Limit Exceeded")
        )
        mock_model_class.return_value = mock_model

        gemini_service = GeminiService(api_key="test-api-key")

        # When & Then: 적절한 예외가 발생해야 함
        with pytest.raises(ValueError) as exc_info:
            await gemini_service.generate_summary(
                content=sample_content,
                summary_type="general",
                title="테스트"
            )

        assert "Summary generation error" in str(exc_info.value)
        assert "API Rate Limit Exceeded" in str(exc_info.value)

    async def test_different_summary_types(self):
        """다양한 요약 타입별 프롬프트 생성 테스트

        각기 다른 요약 유형에 따라 적절한 지침이 포함되는지 확인합니다.
        """
        with patch('app.services.ai_services.gemini_service.genai.configure'), \
                patch('app.services.ai_services.gemini_service.genai.GenerativeModel'):
            gemini_service = GeminiService(api_key="test-api-key")
            content = "테스트 내용"

            # 각 요약 타입별 프롬프트 확인
            test_cases = [
                ("general", "핵심 내용을 간결하고 명확하게"),
                ("keywords", "주요 키워드와 핵심 개념을 중심으로"),
                ("qa", "Q&A 형식으로 정리"),
                ("study", "학습하기 좋게 구조화하여")
            ]

            for summary_type, expected_instruction in test_cases:
                prompt = gemini_service._build_summary_prompt(
                    content=content,
                    summary_type=summary_type,
                    title="테스트"
                )

                # 각 타입에 맞는 지침이 포함되어 있는지 확인
                assert expected_instruction in prompt
                assert summary_type in prompt
                assert "JSON 형식" in prompt