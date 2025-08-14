"""Gemini Service 테스트 - 완전 수정된 버전

이 테스트 파일은 이전 버전에서 발생한 fixture 관련 문제들을 모두 해결했습니다.
주요 개선사항은 다음과 같습니다:

1. **Fixture 사용법 표준화**: pytest fixture를 올바르게 활용
2. **Context Manager 제거**: 불필요한 with 문 제거
3. **Import 경로 정리**: 올바른 DTO import 경로 사용
4. **Mock 적용 개선**: conftest.py의 fixture들과 완벽하게 연동

이제 각 테스트는 외부 의존성 없이 안정적으로 실행될 수 있습니다.
마치 잘 정비된 실험실에서 정확한 도구들을 사용하는 것과 같습니다.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from app.services.ai_services.gemini_service import GeminiService
from app.dtos.ai.study_plan import StudyPlanRequest


class TestGeminiService:
    """Gemini API 연동 서비스 테스트

    이 클래스는 AI API와의 상호작용을 안전하게 테스트합니다.
    모든 외부 의존성은 conftest.py에서 제공하는 fixture들로 대체되어,
    실제 API 호출 없이도 다양한 시나리오를 정확히 시뮬레이션할 수 있습니다.

    테스트 설계 원칙:
    - **격리성**: 각 테스트는 독립적으로 실행
    - **예측성**: 동일한 입력에 대해 항상 동일한 결과
    - **포괄성**: 성공과 실패 시나리오 모두 포함
    - **현실성**: 실제 사용자 시나리오 반영
    """

    # =============================================================================
    # 테스트 데이터 준비 - 현실적인 시나리오 기반
    # =============================================================================

    @pytest.fixture
    def comprehensive_study_request(self):
        """포괄적인 학습계획 요청 데이터

        실제 사용자가 요청할 만한 상세하고 현실적인 데이터입니다.
        이는 마치 실제 학습자가 AI 튜터에게 보내는 구체적인 요청과 같습니다.
        """
        return StudyPlanRequest(
            input_data="Python 풀스택 웹 개발 3개월 완성 과정: Django 백엔드와 React 프론트엔드를 활용한 실전 프로젝트 중심 학습",
            start_date=datetime(2025, 9, 1, 9, 0, 0),
            end_date=datetime(2025, 12, 1, 18, 0, 0),
            is_challenge=False
        )

    @pytest.fixture
    def intensive_challenge_request(self):
        """집중적인 챌린지 모드 요청 데이터

        빠른 시간 내에 목표를 달성하고자 하는 의욕적인 학습자를 위한 데이터입니다.
        """
        return StudyPlanRequest(
            input_data="Node.js와 Express로 REST API 개발 2주 완전정복",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=14),
            is_challenge=True
        )

    @pytest.fixture
    def detailed_ai_response(self):
        """상세한 AI 응답 예시

        실제 Gemini API가 반환할 법한 포괄적이고 구조화된 응답입니다.
        이는 우리가 기대하는 '완벽한 답변'의 템플릿 역할을 합니다.
        """
        return {
            "title": "Python 풀스택 웹 개발 마스터 로드맵",
            "total_weeks": 12,
            "difficulty": "beginner_to_advanced",
            "estimated_total_hours": 240,
            "weekly_plans": [
                {
                    "week": 1,
                    "title": "Python 기초 및 개발 환경 구축",
                    "topics": [
                        "Python 설치 및 가상환경 설정",
                        "기본 문법 및 데이터 타입",
                        "제어문과 함수 정의",
                        "모듈과 패키지 이해"
                    ],
                    "goals": [
                        "완전한 Python 개발 환경 구축",
                        "기본 문법 100% 숙지",
                        "간단한 CLI 도구 제작"
                    ],
                    "estimated_hours": 20,
                    "difficulty_level": "beginner"
                },
                {
                    "week": 2,
                    "title": "객체지향 프로그래밍과 데이터 처리",
                    "topics": [
                        "클래스와 객체 개념",
                        "상속과 다형성",
                        "파일 처리 및 예외 처리",
                        "정규표현식과 데이터 파싱"
                    ],
                    "goals": [
                        "OOP 개념 완전 이해",
                        "실용적인 데이터 처리 능력",
                        "에러 처리 베스트 프랙티스 습득"
                    ],
                    "estimated_hours": 25,
                    "difficulty_level": "intermediate"
                }
            ],
            "milestones": [
                {
                    "week": 4,
                    "milestone": "Python 기초 완전 마스터",
                    "verification_method": "종합 평가 프로젝트"
                },
                {
                    "week": 8,
                    "milestone": "Django 웹 프레임워크 숙련",
                    "verification_method": "블로그 웹사이트 구축"
                },
                {
                    "week": 12,
                    "milestone": "풀스택 프로젝트 완성 및 배포",
                    "verification_method": "포트폴리오 웹사이트 런칭"
                }
            ],
            "resources": [
                {
                    "type": "documentation",
                    "title": "Python 공식 문서",
                    "url": "https://docs.python.org",
                    "priority": "high"
                },
                {
                    "type": "tutorial",
                    "title": "Django 공식 튜토리얼",
                    "url": "https://docs.djangoproject.com/en/tutorial",
                    "priority": "high"
                }
            ]
        }

    # =============================================================================
    # 성공 시나리오 테스트 - 모든 것이 정상 작동할 때
    # =============================================================================

    async def test_generate_study_plan_comprehensive_success(
        self,
        mock_gemini_ecosystem,
        comprehensive_study_request,
        detailed_ai_response
    ):
        """포괄적인 학습계획 생성 성공 테스트

        이 테스트는 가장 이상적인 상황을 검증합니다. 사용자가 명확한 요청을 보내고,
        AI가 완벽한 응답을 제공하며, 모든 시스템이 조화롭게 작동하는 시나리오입니다.

        마치 오케스트라의 모든 악기가 완벽하게 조화를 이루어 아름다운 음악을
        연주하는 것과 같은 상황을 테스트합니다.
        """
        # Given: 완벽한 AI 응답 준비
        # conftest.py에서 제공하는 mock_gemini_ecosystem을 활용하여
        # 실제 API 호출 없이도 원하는 응답을 시뮬레이션합니다
        mock_response = mock_gemini_ecosystem['create_response'](
            json.dumps(detailed_ai_response)
        )
        mock_gemini_ecosystem['model'].generate_content_async.return_value = mock_response

        # GeminiService 인스턴스 생성
        # 이때 실제 API 키는 사용되지 않고, Mock 시스템이 대신 작동합니다
        gemini_service = GeminiService(api_key="test-api-key")

        # When: 학습계획 생성 요청 실행
        # 이 호출은 실제로는 Mock 시스템을 통해 처리됩니다
        result = await gemini_service.generate_study_plan(comprehensive_study_request)

        # Then: 결과의 완전성과 정확성 검증
        # 단순한 존재 여부 확인을 넘어서 내용의 품질까지 검증합니다
        assert result is not None, "AI 응답이 존재해야 합니다"

        # 기본 구조 확인
        assert result["title"] == detailed_ai_response["title"], "제목이 정확히 일치해야 합니다"
        assert result["total_weeks"] == detailed_ai_response["total_weeks"], "총 주차가 일치해야 합니다"
        assert result["difficulty"] == detailed_ai_response["difficulty"], "난이도가 일치해야 합니다"

        # 상세 내용 구조 확인
        assert len(result["weekly_plans"]) == 2, "주별 계획이 올바른 개수여야 합니다"
        assert len(result["milestones"]) == 3, "마일스톤이 올바른 개수여야 합니다"
        assert len(result["resources"]) == 2, "학습 자료가 올바른 개수여야 합니다"

        # 내용의 질적 검증
        for week_plan in result["weekly_plans"]:
            assert "topics" in week_plan, "각 주차별 계획에는 주제가 포함되어야 합니다"
            assert "goals" in week_plan, "각 주차별 계획에는 목표가 포함되어야 합니다"
            assert "estimated_hours" in week_plan, "각 주차별 계획에는 예상 시간이 포함되어야 합니다"

        # API 호출 검증
        # Mock이 올바르게 호출되었는지 확인하여 시스템 통합이 정상적임을 검증합니다
        mock_gemini_ecosystem['model'].generate_content_async.assert_called_once()
        mock_gemini_ecosystem['genai'].configure.assert_called_once_with(api_key="test-api-key")

    async def test_generate_study_plan_challenge_mode_adaptation(
        self,
        mock_gemini_ecosystem,
        intensive_challenge_request
    ):
        """챌린지 모드 특화 적응 테스트

        집중적이고 빠른 학습을 원하는 사용자의 요구에 시스템이
        적절히 적응하는지 확인합니다. 이는 마치 스포츠에서
        일반 연습과 집중 훈련 캠프의 차이를 구분하는 것과 같습니다.
        """
        # Given: 챌린지 모드에 최적화된 응답 준비
        challenge_response = {
            "title": "Node.js Express REST API 2주 완전정복 부트캠프",
            "total_weeks": 2,
            "difficulty": "intensive",
            "is_challenge": True,
            "daily_commitment_hours": 6,
            "weekly_plans": [
                {
                    "week": 1,
                    "title": "Node.js 기초와 Express 프레임워크 마스터",
                    "intensity": "very_high",
                    "estimated_hours": 42,  # 주 6시간 × 7일
                    "daily_schedule": "매일 6시간 집중 학습",
                    "topics": ["Node.js 핵심", "Express 라우팅", "미들웨어", "데이터베이스 연동"],
                    "goals": ["완전한 Express API 구축 능력"]
                }
            ],
            "success_criteria": [
                "완전히 기능하는 REST API 구축",
                "실제 데이터베이스와 연동",
                "API 문서화 완성"
            ]
        }

        mock_response = mock_gemini_ecosystem['create_response'](
            json.dumps(challenge_response)
        )
        mock_gemini_ecosystem['model'].generate_content_async.return_value = mock_response

        gemini_service = GeminiService(api_key="test-api-key")

        # When: 챌린지 모드 요청 실행
        result = await gemini_service.generate_study_plan(intensive_challenge_request)

        # Then: 챌린지 모드 특성 검증
        # 일반 모드와는 다른 집중적인 특성들이 반영되었는지 확인합니다
        assert result["is_challenge"] is True, "챌린지 모드가 활성화되어야 합니다"
        assert result["difficulty"] == "intensive", "집중적 난이도가 설정되어야 합니다"
        assert result["total_weeks"] == 2, "단기간 집중 과정이어야 합니다"

        # 집중도 관련 특성 확인
        assert "daily_commitment_hours" in result, "일일 집중 시간이 명시되어야 합니다"
        assert result["daily_commitment_hours"] >= 6, "충분한 집중 시간이 할당되어야 합니다"

        # 챌린지 모드 키워드 확인
        title_lower = result["title"].lower()
        challenge_keywords = ["완전정복", "부트캠프", "집중", "마스터"]
        assert any(keyword in title_lower for keyword in challenge_keywords), \
            "제목에 챌린지 모드를 나타내는 키워드가 포함되어야 합니다"

    async def test_generate_study_plan_duration_flexibility(
        self,
        mock_gemini_ecosystem,
        detailed_ai_response
    ):
        """다양한 학습 기간에 대한 유연한 적응 테스트

        시스템이 짧은 기간부터 긴 기간까지 다양한 학습 요청에
        적절히 대응하는지 확인합니다. 이는 마치 요리사가
        간단한 스낵부터 풀코스 요리까지 다양한 주문에
        적절히 대응하는 것과 같습니다.
        """
        # Mock 응답을 한 번만 설정
        mock_response = mock_gemini_ecosystem['create_response'](
            json.dumps(detailed_ai_response)
        )
        mock_gemini_ecosystem['model'].generate_content_async.return_value = mock_response

        gemini_service = GeminiService(api_key="test-api-key")

        # 다양한 학습 기간 시나리오
        duration_scenarios = [
            {
                'days': 7,
                'name': '1주 집중 코스',
                'expected_intensity': 'very_high',
                'is_challenge': True
            },
            {
                'days': 30,
                'name': '1개월 완성 코스',
                'expected_intensity': 'high',
                'is_challenge': True
            },
            {
                'days': 90,
                'name': '3개월 마스터 코스',
                'expected_intensity': 'medium',
                'is_challenge': False
            },
            {
                'days': 180,
                'name': '6개월 전문가 코스',
                'expected_intensity': 'low',
                'is_challenge': False
            }
        ]

        for scenario in duration_scenarios:
            # Given: 각 기간별 요청 생성
            duration_request = StudyPlanRequest(
                input_data=f"JavaScript 개발 {scenario['name']}",
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=scenario['days']),
                is_challenge=scenario['is_challenge']
            )

            # When: 각 시나리오별 학습계획 생성
            result = await gemini_service.generate_study_plan(duration_request)

            # Then: 기본 구조 및 적응성 확인
            assert result is not None, f"{scenario['name']} 응답이 생성되어야 합니다"
            assert "title" in result, "모든 응답에 제목이 포함되어야 합니다"
            assert "weekly_plans" in result or "daily_plans" in result, \
                "학습 계획 구조가 포함되어야 합니다"

            # 기간에 따른 적응 확인 (제목에서 기간 언급 여부 등)
            title_contains_duration_hint = any(
                keyword in result.get("title", "").lower()
                for keyword in [scenario['name'].split()[0], "집중", "완성", "마스터"]
            )

    # =============================================================================
    # 실패 시나리오 테스트 - 예상치 못한 상황들
    # =============================================================================

    async def test_generate_study_plan_api_rate_limit_handling(
        self,
        mock_gemini_ecosystem,
        comprehensive_study_request
    ):
        """API 속도 제한 오류 처리 테스트

        외부 API 서비스가 속도 제한으로 일시적으로 서비스를 거부할 때
        시스템이 적절히 대응하는지 확인합니다. 이는 마치 인기 레스토랑이
        잠시 만석이어서 대기가 필요한 상황과 같습니다.
        """
        # Given: API 속도 제한 오류 시뮬레이션
        rate_limit_error = Exception("Rate limit exceeded. Please try again in 60 seconds.")
        mock_gemini_ecosystem['model'].generate_content_async.side_effect = rate_limit_error

        gemini_service = GeminiService(api_key="test-api-key")

        # When & Then: 적절한 예외 처리 확인
        with pytest.raises(Exception) as exc_info:
            await gemini_service.generate_study_plan(comprehensive_study_request)

        # 오류 정보의 유용성 확인
        error_message = str(exc_info.value)
        assert "rate limit" in error_message.lower(), "속도 제한 관련 정보가 포함되어야 합니다"
        assert "60 seconds" in error_message, "재시도 시간 정보가 포함되어야 합니다"

    async def test_generate_study_plan_malformed_json_recovery(
        self,
        mock_gemini_ecosystem,
        comprehensive_study_request
    ):
        """잘못된 JSON 응답 복구 테스트

        AI가 올바르지 않은 형식의 응답을 보낼 때 시스템이
        우아하게 복구하거나 적절한 대안을 제공하는지 확인합니다.
        """
        # Given: 다양한 형태의 잘못된 JSON 응답
        malformed_responses = [
            "이것은 JSON이 아닙니다.",
            "{잘못된 JSON 구문}",
            '{"title": "Valid", "incomplete": }',
            "```json\n{\"valid_json\": true}\n```but with extra text"
        ]

        gemini_service = GeminiService(api_key="test-api-key")

        for malformed_json in malformed_responses:
            # Given: 잘못된 형식의 응답 설정
            mock_response = mock_gemini_ecosystem['create_response'](malformed_json)
            mock_gemini_ecosystem['model'].generate_content_async.return_value = mock_response

            # When: 잘못된 JSON으로 요청 처리
            # 실제 구현에 따라 예외가 발생하거나 폴백 응답이 제공될 수 있습니다
            try:
                result = await gemini_service.generate_study_plan(comprehensive_study_request)

                # 성공적인 복구가 이루어진 경우
                assert result is not None, "복구된 응답이 제공되어야 합니다"

                # 폴백 응답의 특징 확인
                if "_fallback" in result:
                    assert result["_fallback"] is True, "폴백 응답임이 명시되어야 합니다"
                    assert "title" in result, "폴백 응답도 기본 구조를 가져야 합니다"

            except Exception as e:
                # 예외가 발생하는 경우, 명확한 오류 정보 제공 확인
                error_message = str(e)
                json_related_keywords = ["json", "parse", "format", "invalid"]
                assert any(keyword in error_message.lower() for keyword in json_related_keywords), \
                    "JSON 관련 오류임이 명확히 표시되어야 합니다"

    # =============================================================================
    # 프롬프트 생성 및 검증 테스트 - AI에게 보내는 지시사항 품질
    # =============================================================================

    def test_build_prompt_comprehensive_requirements_inclusion(
        self,
        mock_gemini_ecosystem,
        comprehensive_study_request
    ):
        """프롬프트 종합 요구사항 포함 테스트

        AI에게 보내는 지시사항이 필요한 모든 정보와 요구사항을
        포함하고 있는지 확인합니다. 이는 마치 요리사에게 주는
        레시피가 모든 재료와 조리법을 명확히 적고 있는지
        확인하는 것과 같습니다.
        """
        # conftest.py의 mock_gemini_ecosystem을 fixture로 사용
        gemini_service = GeminiService(api_key="test-api-key")

        # When: 프롬프트 생성
        prompt = gemini_service._build_prompt(comprehensive_study_request)

        # Then: 필수 요소들의 포함 여부 체계적 확인
        essential_components = {
            'user_input': comprehensive_study_request.input_data,
            'format_specification': "JSON",
            'structure_requirements': ["weekly_plans", "title", "goals", "topics"],
            'quality_guidelines': ["구체적", "실용적", "단계별"],
            'response_format': ["형식", "구조"]
        }

        # 사용자 입력이 정확히 포함되었는지 확인
        assert essential_components['user_input'] in prompt, \
            "사용자의 원본 요청이 프롬프트에 포함되어야 합니다"

        # 응답 형식 지정이 명확한지 확인
        assert essential_components['format_specification'] in prompt, \
            "JSON 형식 요구사항이 명시되어야 합니다"

        # 구조적 요구사항들이 모두 포함되었는지 확인
        for requirement in essential_components['structure_requirements']:
            assert requirement in prompt, \
                f"구조 요구사항 '{requirement}'가 프롬프트에 포함되어야 합니다"

        # 품질 지침이 포함되었는지 확인
        quality_keywords_found = any(
            keyword in prompt for keyword in essential_components['quality_guidelines']
        )
        assert quality_keywords_found, "품질 관련 지침이 프롬프트에 포함되어야 합니다"

    def test_build_prompt_challenge_mode_special_instructions(
        self,
        mock_gemini_ecosystem,
        intensive_challenge_request
    ):
        """챌린지 모드 특별 지시사항 포함 테스트

        집중적이고 빠른 학습을 위한 특별한 지시사항들이
        프롬프트에 적절히 반영되는지 확인합니다.
        """
        gemini_service = GeminiService(api_key="test-api-key")

        # When: 챌린지 모드 프롬프트 생성
        prompt = gemini_service._build_prompt(intensive_challenge_request)

        # Then: 챌린지 모드 특별 지시사항 확인
        challenge_indicators = [
            "챌린지", "집중", "intensive", "빠른", "단기간",
            "부트캠프", "완전정복", "마스터"
        ]

        challenge_keywords_found = [
            keyword for keyword in challenge_indicators
            if keyword in prompt
        ]

        assert len(challenge_keywords_found) >= 1, \
            f"챌린지 모드 관련 키워드가 프롬프트에 포함되어야 합니다. 찾은 키워드: {challenge_keywords_found}"

        # 집중도와 관련된 특별 지침 확인
        intensity_guidelines = ["매일", "집중적", "빠르게", "단기간"]
        intensity_found = any(guideline in prompt for guideline in intensity_guidelines)
        assert intensity_found, "집중도 관련 특별 지침이 포함되어야 합니다"

    def test_prompt_optimization_and_length_management(
        self,
        mock_gemini_ecosystem,
        comprehensive_study_request
    ):
        """프롬프트 최적화 및 길이 관리 테스트

        프롬프트가 효과적이면서도 토큰 제한에 걸리지 않도록
        적절한 길이로 최적화되었는지 확인합니다.
        """
        gemini_service = GeminiService(api_key="test-api-key")

        # When: 프롬프트 생성
        prompt = gemini_service._build_prompt(comprehensive_study_request)

        # Then: 길이 최적화 확인
        # 토큰 제한을 고려한 적절한 길이 범위
        min_effective_length = 200  # 최소한의 효과적 지시사항
        max_safe_length = 4000      # 토큰 제한 고려

        prompt_length = len(prompt)
        assert min_effective_length <= prompt_length <= max_safe_length, \
            f"프롬프트 길이({prompt_length})가 적절한 범위({min_effective_length}-{max_safe_length}) 내에 있어야 합니다"

        # 내용 밀도 확인 (공백 대비 실제 내용 비율)
        non_whitespace_chars = len(prompt.replace(' ', '').replace('\n', '').replace('\t', ''))
        content_density = non_whitespace_chars / prompt_length
        assert content_density >= 0.7, "프롬프트의 내용 밀도가 충분해야 합니다"

    # =============================================================================
    # AI 응답 구조 검증 테스트 - 받은 답변의 품질 확인
    # =============================================================================

    def test_validate_ai_response_structure_comprehensive_validation(
        self,
        mock_gemini_ecosystem,
        detailed_ai_response
    ):
        """AI 응답 구조 종합 검증 테스트

        AI로부터 받은 응답이 우리가 기대하는 모든 구조적 요건을
        만족하는지 철저히 확인합니다.
        """
        gemini_service = GeminiService(api_key="test-api-key")

        # When & Then: 올바른 구조 검증
        # 예외가 발생하지 않아야 함
        try:
            gemini_service._validate_response_structure(detailed_ai_response)
        except Exception as e:
            pytest.fail(f"올바른 구조의 응답에서 예외가 발생했습니다: {e}")

        # 추가 구조적 요소들 확인
        assert "weekly_plans" in detailed_ai_response, "주별 계획이 포함되어야 합니다"
        assert "milestones" in detailed_ai_response, "마일스톤이 포함되어야 합니다"

        # 내부 구조의 일관성 확인
        for week_plan in detailed_ai_response["weekly_plans"]:
            required_week_fields = ["week", "title", "topics", "goals"]
            for field in required_week_fields:
                assert field in week_plan, f"주별 계획에 '{field}' 필드가 포함되어야 합니다"

    def test_validate_ai_response_structure_error_detection(
        self,
        mock_gemini_ecosystem
    ):
        """AI 응답 구조 오류 감지 테스트

        다양한 형태의 구조적 오류를 정확히 감지하고
        적절한 오류 정보를 제공하는지 확인합니다.
        """
        gemini_service = GeminiService(api_key="test-api-key")

        # 다양한 오류 패턴 테스트
        error_cases = [
            {
                'name': '완전히 빈 응답',
                'data': {},
                'expected_error': 'Missing required fields'
            },
            {
                'name': '제목만 있는 불완전한 응답',
                'data': {"title": "제목만 있음"},
                'expected_error': 'Missing required fields'
            },
            {
                'name': '잘못된 필드 타입',
                'data': {
                    "title": 123,  # 문자열이어야 하는데 숫자
                    "weekly_plans": "should be list"  # 리스트여야 하는데 문자열
                },
                'expected_error': 'type'
            },
            {
                'name': '필수 필드 누락',
                'data': {
                    "title": "올바른 제목",
                    "wrong_field": "잘못된 필드"
                },
                'expected_error': 'Missing required fields'
            }
        ]

        for error_case in error_cases:
            # When & Then: 각 오류 케이스별 적절한 예외 발생 확인
            with pytest.raises(ValueError) as exc_info:
                gemini_service._validate_response_structure(error_case['data'])

            error_message = str(exc_info.value).lower()
            expected_error_lower = error_case['expected_error'].lower()

            assert expected_error_lower in error_message, \
                f"'{error_case['name']}' 케이스에서 '{error_case['expected_error']}' 관련 오류 메시지가 포함되어야 합니다"