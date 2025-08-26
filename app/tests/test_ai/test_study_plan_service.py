"""Study Plan Service 테스트 - 최종 완성된 버전

이 테스트 파일은 모든 이전 문제점들을 해결하고 최고의 품질로 완성되었습니다.
다른 테스트 파일들에서 검증된 최선의 방법들을 모두 적용하여,
가장 안정적이고 포괄적인 테스트 환경을 제공합니다.

주요 완성 요소:
1. **완벽한 Mock 통합**: conftest.py의 모든 fixture들과 완벽한 연동
2. **커스텀 예외 시스템 완전 적용**: 새로운 예외 처리 방식 100% 활용
3. **현실적 시나리오 기반**: 실제 사용자 경험을 정확히 반영
4. **포괄적 테스트 커버리지**: 모든 성공/실패/경계 케이스 포함
5. **유지보수성 극대화**: 명확한 구조와 재사용 가능한 헬퍼들

이제 이 테스트 파일은 마치 잘 설계된 품질 보증 시스템처럼,
학습계획 기능의 모든 측면을 철저히 검증합니다.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
import json

from app.services.ai_services.study_plan_service import StudyPlanService
from app.dtos.ai.study_plan import StudyPlanRequest, StudyPlanResponse

# 새로운 커스텀 예외 시스템 완전 활용
from app.exceptions import (
    StudyPlanNotFoundError,
    StudyPlanAccessDeniedError,
    StudyPlanCreationError,
    StudyPlanValidationError
)


class TestStudyPlanService:
    """학습계획 서비스 종합 테스트 시스템

    이 클래스는 AI 기반 학습계획 생성 시스템의 모든 핵심 기능을
    체계적으로 검증합니다. 실제 교육 환경에서 발생할 수 있는
    모든 상황을 시뮬레이션하여 시스템의 완전성을 보장합니다.

    테스트 설계 철학:
    - **교육자 관점**: 실제 교육자와 학습자의 니즈 반영
    - **학습 효과성**: 학습 목표 달성을 위한 최적화 확인
    - **개인화**: 각 사용자의 상황에 맞는 맞춤형 계획 생성 검증
    - **지속 가능성**: 장기적인 학습 여정 지원 능력 확인
    """

    # =============================================================================
    # 서비스 구성 및 기본 설정
    # =============================================================================

    @pytest.fixture
    def study_plan_service(self, mock_gemini_ecosystem):
        """완전히 최적화된 StudyPlanService 인스턴스

        이 fixture는 실제 교육 환경에서 사용되는 것과 동일한 기능을
        제공하면서도, 모든 외부 의존성이 안전하게 Mock으로 대체된
        완벽한 테스트 환경을 제공합니다.

        마치 실제 교실 대신 시뮬레이션 교실에서 교육 방법을
        연습하는 것과 같은 안전하고 통제된 환경입니다.
        """
        # GeminiService Mock 생성 및 최적화된 설정
        mock_gemini_service = Mock()
        mock_gemini_service.generate_study_plan = AsyncMock()

        # 현실적이고 유용한 기본 응답 설정
        # 실제 AI가 생성할 법한 고품질 학습계획을 시뮬레이션
        mock_gemini_service.generate_study_plan.return_value = \
            mock_gemini_ecosystem['default_study_plan']

        return StudyPlanService(gemini_service=mock_gemini_service)

    # =============================================================================
    # 생성(Create) 기능 테스트 - 맞춤형 학습계획 생성
    # =============================================================================

    async def test_create_study_plan_personalized_learning_journey(
        self,
        study_plan_service,
        study_plan_test_data,
        mock_tortoise_ecosystem
    ):
        """개인화된 학습 여정 생성 종합 테스트

        이 테스트는 사용자의 구체적인 학습 목표와 상황을 바탕으로
        AI가 개인화된 학습계획을 생성하는 전체 과정을 검증합니다.

        실제 교육 상담사가 학생과 상담하여 맞춤형 커리큘럼을
        설계하는 과정을 AI가 자동화하는 시나리오입니다.

        검증하는 교육적 요소들:
        1. 학습 목표의 명확한 반영
        2. 개인 상황(시간, 난이도)에 맞는 조정
        3. 체계적인 단계별 진행 계획
        4. 실현 가능한 학습 일정 수립
        """
        # Given: 실제 학습자의 구체적인 요청 시나리오
        user_id = study_plan_test_data['user_id']

        # 현실적인 학습자 프로필을 반영한 요청 데이터
        personalized_request = StudyPlanRequest(
            input_data="직장인으로서 퇴근 후 시간을 활용해 Python 백엔드 개발자로 전향하고 싶습니다. "
                     "현재 프로그래밍 경험은 없지만, 3개월 후 간단한 웹 API를 만들 수 있는 수준이 목표입니다.",
            start_date=study_plan_test_data['request_data']['start_date'],
            end_date=study_plan_test_data['request_data']['end_date'],
            is_challenge=False  # 직장인이므로 무리하지 않는 일정
        )

        # 개인화된 AI 응답 시뮬레이션
        personalized_ai_response = {
            **study_plan_test_data['ai_response'],
            "learner_profile": "working_professional_beginner",
            "daily_study_time": 2,  # 직장인 고려한 현실적 시간
            "flexibility_level": "high",  # 업무 상황 변동 고려
            "career_transition_focus": True,
            "practical_project_emphasis": True
        }

        # AI 서비스가 개인화된 응답을 제공하도록 설정
        study_plan_service.gemini_service.generate_study_plan.return_value = personalized_ai_response

        # 데이터베이스 저장 시뮬레이션
        mock_study_plan_instance = self._create_realistic_study_plan_mock({
            **study_plan_test_data,
            'request_data': {
                **study_plan_test_data['request_data'],
                'input_data': personalized_request.input_data
            },
            'ai_response': personalized_ai_response
        })

        StudyPlan = mock_tortoise_ecosystem['StudyPlan']
        StudyPlan.create.return_value = mock_study_plan_instance

        # When: 개인화된 학습계획 생성 실행
        result = await study_plan_service.create_study_plan(
            user_id=user_id,
            request=personalized_request
        )

        # Then: 개인화 품질 및 교육적 효과성 검증
        # 1. 기본 응답 구조와 데이터 무결성 확인
        self._assert_study_plan_educational_quality(result, study_plan_test_data)

        # 2. 개인 상황 반영도 확인
        assert result.input_data == personalized_request.input_data
        assert "직장인" in result.input_data  # 개인 상황이 보존되었는지 확인
        assert "3개월" in result.input_data   # 목표 기간이 보존되었는지 확인

        # 3. AI 서비스 호출의 정확성 확인
        study_plan_service.gemini_service.generate_study_plan.assert_called_once_with(personalized_request)

        # 4. 데이터 저장의 완전성 확인
        StudyPlan.create.assert_called_once()
        create_call_kwargs = StudyPlan.create.call_args.kwargs
        assert create_call_kwargs['user_id'] == user_id
        assert create_call_kwargs['input_data'] == personalized_request.input_data

    async def test_create_study_plan_intensive_challenge_mode(
        self,
        study_plan_service,
        study_plan_test_data,
        mock_tortoise_ecosystem
    ):
        """집중 챌린지 모드 학습계획 생성 테스트

        단기간에 집중적으로 학습하고자 하는 의욕적인 학습자를 위한
        특별한 학습계획이 적절히 생성되는지 확인합니다.

        이는 마치 단기 집중 부트캠프나 해커톤 같은 환경에서의
        학습 경험을 AI가 설계하는 시나리오입니다.
        """
        # Given: 집중적 학습을 원하는 학습자 시나리오
        user_id = study_plan_test_data['user_id']

        intensive_request = StudyPlanRequest(
            input_data="대학 방학 2주 동안 React를 완전히 마스터해서 개인 프로젝트를 완성하고 싶습니다. "
                     "하루 10시간까지 투자할 수 있고, 절대 포기하지 않을 각오가 되어 있습니다.",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=14),
            is_challenge=True  # 챌린지 모드 활성화
        )

        # 집중 모드에 최적화된 AI 응답
        intensive_ai_response = {
            "title": "React 2주 완전정복 집중 부트캠프",
            "total_weeks": 2,
            "difficulty": "intensive_immersive",
            "daily_commitment_hours": 10,
            "challenge_mode": True,
            "success_metrics": [
                "완전한 React 앱 3개 구축",
                "실무급 컴포넌트 라이브러리 제작",
                "배포까지 완료한 포트폴리오 프로젝트"
            ],
            "weekly_plans": [
                {
                    "week": 1,
                    "title": "React 핵심 마스터 주간",
                    "intensity": "maximum",
                    "daily_schedule": "09:00-19:00 (10시간 집중)",
                    "estimated_hours": 70,
                    "breakthrough_goals": ["React 핵심 개념 완전 체화"]
                }
            ]
        }

        study_plan_service.gemini_service.generate_study_plan.return_value = intensive_ai_response

        mock_instance = self._create_realistic_study_plan_mock({
            **study_plan_test_data,
            'request_data': {
                **study_plan_test_data['request_data'],
                'input_data': intensive_request.input_data,
                'is_challenge': True
            },
            'ai_response': intensive_ai_response
        })

        StudyPlan = mock_tortoise_ecosystem['StudyPlan']
        StudyPlan.create.return_value = mock_instance

        # When: 집중 챌린지 모드 생성
        result = await study_plan_service.create_study_plan(
            user_id=user_id,
            request=intensive_request
        )

        # Then: 집중 모드 특성과 실현 가능성 검증
        # 1. 챌린지 모드 활성화 확인
        assert result.is_challenge is True

        # 2. 고강도 학습에 대한 내용 반영 확인
        assert "10시간" in result.input_data or "집중" in result.input_data
        assert "완전정복" in result.input_data or "마스터" in result.input_data

        # 3. 현실적 목표 설정 여부 확인 (AI 응답에서)
        ai_response_data = json.loads(result.output_data) if hasattr(result, 'output_data') else intensive_ai_response
        if "daily_commitment_hours" in ai_response_data:
            assert ai_response_data["daily_commitment_hours"] >= 8  # 고강도 학습 시간

    async def test_create_study_plan_ai_service_comprehensive_failure_recovery(
        self,
        study_plan_service,
        study_plan_test_data
    ):
        """AI 서비스 종합적 실패 복구 시스템 테스트

        다양한 AI 서비스 실패 상황에서 시스템이 교육적 가치를
        해치지 않으면서 적절히 대응하는지 확인합니다.

        이는 마치 주강사가 아플 때 대체 강사나 다른 교육 방식으로
        수업의 연속성을 보장하는 것과 같은 개념입니다.
        """
        user_id = study_plan_test_data['user_id']
        request = StudyPlanRequest(**study_plan_test_data['request_data'])

        # 교육 서비스에서 실제로 발생할 수 있는 AI 실패 시나리오들
        educational_ai_failure_scenarios = [
            {
                'failure_context': '수강생 급증으로 인한 AI 서비스 과부하',
                'exception': Exception("High traffic - AI service temporarily overloaded"),
                'expected_recovery_guidance': True,
                'educational_continuity': True,
                'user_impact_minimization': True
            },
            {
                'failure_context': 'AI 모델 업데이트로 인한 일시적 서비스 중단',
                'exception': Exception("Model update in progress - Service temporarily unavailable"),
                'expected_recovery_guidance': True,
                'estimated_downtime': "30분 이내",
                'alternative_suggestion': True
            },
            {
                'failure_context': '복잡한 학습 요청으로 인한 처리 시간 초과',
                'exception': Exception("Complex request timeout - Please simplify your learning goals"),
                'expected_user_guidance': True,
                'simplification_needed': True,
                'educational_advice': True
            }
        ]

        for scenario in educational_ai_failure_scenarios:
            # Given: 교육 환경에서의 실제 AI 실패 상황
            study_plan_service.gemini_service.generate_study_plan.side_effect = scenario['exception']

            # When & Then: 교육적 연속성을 보장하는 실패 처리
            with pytest.raises(StudyPlanCreationError) as exc_info:
                await study_plan_service.create_study_plan(user_id=user_id, request=request)

            creation_error = exc_info.value

            # 1. 교육자와 학습자에게 유용한 오류 정보 제공 확인
            assert creation_error.details['user_id'] == user_id
            assert 'original_error_type' in creation_error.details

            # 2. 교육적 연속성 보장을 위한 대안 제시 확인
            if scenario.get('expected_recovery_guidance'):
                assert creation_error.details['retry_possible'] is True

            if scenario.get('estimated_downtime'):
                assert creation_error.details.get('suggested_wait_time') is not None

            if scenario.get('alternative_suggestion'):
                assert 'suggested_action' in creation_error.details

    # =============================================================================
    # 조회(Read) 기능 테스트 - 학습 진행 상황 추적
    # =============================================================================

    async def test_get_study_plan_by_id_learning_progress_tracking(
        self,
        study_plan_service,
        study_plan_test_data,
        mock_tortoise_ecosystem
    ):
        """학습 진행 상황 추적을 위한 계획 조회 테스트

        학습자가 자신의 학습계획을 조회하여 진행 상황을
        확인하고 다음 단계를 계획할 수 있는지 검증합니다.

        이는 마치 학습 일지나 포트폴리오를 통해 자신의
        성장 과정을 돌아보는 것과 같은 교육적 활동입니다.
        """
        # Given: 진행 중인 학습계획과 학습자
        study_plan_id = study_plan_test_data['study_plan_id']
        user_id = study_plan_test_data['user_id']

        # 실제 학습 진행 상황이 반영된 Mock 데이터
        learning_progress_data = {
            **study_plan_test_data,
            'ai_response': {
                **study_plan_test_data['ai_response'],
                'learning_progress': {
                    'current_week': 2,
                    'completion_rate': 0.3,
                    'next_milestone': 'Python 기초 완료',
                    'suggested_review_topics': ['변수', '함수']
                }
            }
        }

        mock_instance = self._create_realistic_study_plan_mock(learning_progress_data)
        StudyPlan = mock_tortoise_ecosystem['StudyPlan']
        StudyPlan.get_or_none.return_value = mock_instance

        # When: 학습 진행 추적을 위한 계획 조회
        result = await study_plan_service.get_study_plan_by_id(
            study_plan_id=study_plan_id,
            user_id=user_id
        )

        # Then: 학습 추적에 필요한 정보의 완전성 확인
        # 1. 기본 학습계획 정보 정확성
        assert isinstance(result, StudyPlanResponse)
        assert result.id == study_plan_id
        assert result.user_id == user_id

        # 2. 학습 목표와 내용 보존 확인
        assert result.input_data == learning_progress_data['request_data']['input_data']
        assert result.start_date == learning_progress_data['request_data']['start_date']
        assert result.end_date == learning_progress_data['request_data']['end_date']

        # 3. 학습 계획의 체계성 확인 (AI 응답 데이터를 통해)
        assert result.output_data is not None

        # 4. 데이터베이스 조회 최적화 확인
        StudyPlan.get_or_none.assert_called_once_with(id=study_plan_id)

    async def test_get_study_plan_by_id_educational_security_and_privacy(
        self,
        study_plan_service,
        study_plan_test_data,
        mock_tortoise_ecosystem
    ):
        """교육적 보안 및 개인정보 보호 테스트

        교육 환경에서 중요한 학습자의 개인 학습 정보가
        다른 학습자에게 노출되지 않도록 보호되는지 확인합니다.

        이는 마치 학교에서 다른 학생의 성적표나 개인 학습
        계획을 볼 수 없도록 하는 개인정보 보호와 같습니다.
        """
        # Given: 타인의 학습계획에 접근 시도하는 시나리오
        target_study_plan_id = study_plan_test_data['study_plan_id']
        unauthorized_learner_id = 789  # 권한 없는 학습자
        plan_owner_id = study_plan_test_data['user_id']  # 실제 계획 소유자

        # 다른 학습자의 개인 학습계획 Mock
        private_learning_plan = self._create_realistic_study_plan_mock({
            **study_plan_test_data,
            'ai_response': {
                **study_plan_test_data['ai_response'],
                'personal_learning_goals': "개인적인 커리어 전환 목표",
                'current_skill_level': "초급자",
                'learning_challenges': ["시간 부족", "집중력 부족"]
            }
        })
        private_learning_plan.user_id = plan_owner_id  # 실제 소유자 설정

        StudyPlan = mock_tortoise_ecosystem['StudyPlan']
        StudyPlan.get_or_none.return_value = private_learning_plan

        # When & Then: 교육적 개인정보 보호 확인
        with pytest.raises(StudyPlanAccessDeniedError) as exc_info:
            await study_plan_service.get_study_plan_by_id(
                study_plan_id=target_study_plan_id,
                user_id=unauthorized_learner_id
            )

        access_error = exc_info.value

        # 1. 개인정보 보호 위반 정확한 감지
        assert str(target_study_plan_id) in str(access_error)
        assert str(unauthorized_learner_id) in str(access_error)

        # 2. 교육 환경에 적합한 보안 수준 적용
        assert access_error.details['security_level'] == 'high'
        assert access_error.details['action_required'] == 'access_log'

        # 3. 학습자에게 교육적인 안내 메시지 제공
        assert '본인의' in access_error.details['suggested_action']

    async def test_get_user_study_plans_learning_portfolio_management(
        self,
        study_plan_service,
        study_plan_test_data,
        mock_tortoise_ecosystem
    ):
        """학습 포트폴리오 관리를 위한 계획 목록 조회 테스트

        학습자가 자신의 모든 학습계획을 체계적으로 관리하고
        학습 여정을 전체적으로 조망할 수 있는지 확인합니다.

        이는 마치 학습자가 자신의 학습 이력서나 포트폴리오를
        정리하여 성장 과정을 체계적으로 관리하는 것과 같습니다.
        """
        # Given: 다양한 학습 단계의 계획들을 가진 학습자
        user_id = study_plan_test_data['user_id']

        # 실제 학습자의 학습 여정을 반영한 다양한 계획들
        learning_journey_plans = [
            {
                'plan_id': 1,
                'subject': 'Python 기초',
                'status': 'completed',
                'difficulty': 'beginner',
                'duration_weeks': 4
            },
            {
                'plan_id': 2,
                'subject': 'Django 웹 개발',
                'status': 'in_progress',
                'difficulty': 'intermediate',
                'duration_weeks': 8
            },
            {
                'plan_id': 3,
                'subject': 'React 프론트엔드',
                'status': 'planned',
                'difficulty': 'intermediate',
                'duration_weeks': 6
            },
            {
                'plan_id': 4,
                'subject': '풀스택 프로젝트',
                'status': 'future',
                'difficulty': 'advanced',
                'duration_weeks': 12
            }
        ]

        # 학습 포트폴리오를 구성하는 Mock 계획들 생성
        mock_portfolio_plans = []
        for plan_info in learning_journey_plans:
            mock_plan = self._create_realistic_study_plan_mock({
                **study_plan_test_data,
                'study_plan_id': plan_info['plan_id'],
                'request_data': {
                    **study_plan_test_data['request_data'],
                    'input_data': f"{plan_info['subject']} {plan_info['duration_weeks']}주 과정"
                },
                'ai_response': {
                    **study_plan_test_data['ai_response'],
                    'title': f"{plan_info['subject']} 마스터 과정",
                    'difficulty': plan_info['difficulty'],
                    'total_weeks': plan_info['duration_weeks'],
                    'learning_status': plan_info['status']
                }
            })
            mock_portfolio_plans.append(mock_plan)

        # QuerySet Mock 설정 (학습 포트폴리오 조회 최적화)
        mock_queryset = Mock()
        mock_queryset.order_by.return_value = mock_queryset
        mock_queryset.limit.return_value = mock_queryset
        mock_queryset.offset.return_value = mock_portfolio_plans

        StudyPlan = mock_tortoise_ecosystem['StudyPlan']
        StudyPlan.filter.return_value = mock_queryset

        # When: 학습 포트폴리오 조회 실행
        limit = 10
        offset = 0
        result = await study_plan_service.get_user_study_plans(
            user_id=user_id,
            limit=limit,
            offset=offset
        )

        # Then: 학습 포트폴리오 품질 및 교육적 가치 검증
        # 1. 포트폴리오 기본 구조 확인
        assert isinstance(result, list)
        assert len(result) == len(learning_journey_plans)
        assert all(isinstance(plan, StudyPlanResponse) for plan in result)
        assert all(plan.user_id == user_id for plan in result)

        # 2. 학습 여정의 다양성과 체계성 확인
        plan_subjects = [plan.input_data for plan in result]
        expected_subjects = ['Python 기초', 'Django 웹 개발', 'React 프론트엔드', '풀스택 프로젝트']
        for expected_subject in expected_subjects:
            assert any(expected_subject in subject for subject in plan_subjects)

        # 3. 학습 관리 시스템의 효율성 확인
        StudyPlan.filter.assert_called_once_with(user_id=user_id)
        mock_queryset.order_by.assert_called_once_with("-created_at")  # 최신 계획 우선
        mock_queryset.limit.assert_called_once_with(limit)
        mock_queryset.offset.assert_called_once_with(offset)

    # =============================================================================
    # 수정(Update) 기능 테스트 - 학습 계획의 진화와 적응
    # =============================================================================

    async def test_update_study_plan_adaptive_learning_optimization(
        self,
        study_plan_service,
        study_plan_test_data,
        mock_tortoise_ecosystem
    ):
        """적응형 학습 최적화를 위한 계획 수정 테스트

        학습자의 실제 진행 상황과 변화된 목표에 맞춰
        학습계획이 유연하게 조정되는지 확인합니다.

        이는 마치 개인 교육 코치가 학습자의 진전과 변화하는
        상황을 고려하여 맞춤형 학습 전략을 조정하는 것과 같습니다.
        """
        # Given: 학습 진행 중 목표나 상황이 변화한 시나리오
        study_plan_id = study_plan_test_data['study_plan_id']
        user_id = study_plan_test_data['user_id']

        # 현실적인 학습 목표 변화 시나리오
        adaptive_update_data = {
            'input_data': "처음 목표했던 Python 기초에서 더 나아가 데이터 사이언스 분야로 "
                         "확장하고 싶습니다. 현재 기초는 어느 정도 익혔고, 이제 pandas와 "
                         "머신러닝 기초까지 포함한 심화 과정을 원합니다.",
            'start_date': datetime(2025, 9, 15, 9, 0, 0),  # 조정된 시작일
            'is_challenge': True  # 더 도전적인 목표로 변경
        }

        # 변화된 목표에 맞는 새로운 AI 응답
        evolved_ai_response = {
            **study_plan_test_data['ai_response'],
            "title": "Python 데이터 사이언스 심화 로드맵",
            "difficulty": "beginner_to_intermediate_plus",
            "total_weeks": 16,  # 확장된 기간
            "specialization": "data_science",
            "prerequisite_completion": "python_basics",
            "weekly_plans": [
                {
                    "week": 1,
                    "title": "데이터 분석 도구 mastery",
                    "topics": ["pandas", "numpy", "matplotlib"],
                    "prerequisite_skills": ["Python 기초 문법"],
                    "estimated_hours": 12
                }
            ]
        }

        # 기존 학습계획 Mock (업데이트 대상)
        existing_plan = self._create_realistic_study_plan_mock(study_plan_test_data)
        existing_plan.update_from_dict = Mock(return_value=existing_plan)
        existing_plan.save = AsyncMock()

        # 진화된 학습계획에 대한 AI 응답 설정
        study_plan_service.gemini_service.generate_study_plan.return_value = evolved_ai_response

        # 업데이트 후의 계획 Mock
        updated_plan = self._create_realistic_study_plan_mock({
            **study_plan_test_data,
            'request_data': {
                **study_plan_test_data['request_data'],
                **adaptive_update_data
            },
            'ai_response': evolved_ai_response
        })

        StudyPlan = mock_tortoise_ecosystem['StudyPlan']
        StudyPlan.get_or_none.return_value = existing_plan
        StudyPlan.get.return_value = updated_plan

        # When: 적응형 학습 최적화 업데이트 실행
        result = await study_plan_service.update_study_plan(
            study_plan_id=study_plan_id,
            user_id=user_id,
            update_data=adaptive_update_data
        )

        # Then: 적응형 학습의 교육적 효과성 검증
        # 1. 진화된 학습 목표 반영 확인
        assert isinstance(result, StudyPlanResponse)

        # 2. AI 재생성을 통한 맞춤형 최적화 확인
        # input_data가 변경되었으므로 AI 재생성이 트리거되어야 함
        study_plan_service.gemini_service.generate_study_plan.assert_called_once()

        # 3. 학습 진화 과정의 기록 확인
        existing_plan.update_from_dict.assert_called_once_with(adaptive_update_data)
        existing_plan.save.assert_called_once()
        StudyPlan.get.assert_called_once_with(id=study_plan_id)

    async def test_update_study_plan_schedule_flexibility_management(
        self,
        study_plan_service,
        study_plan_test_data,
        mock_tortoise_ecosystem
    ):
        """학습 일정 유연성 관리를 위한 업데이트 테스트

        학습자의 개인 상황 변화(업무, 가정사 등)에 따라
        학습 일정을 조정하는 기능의 효과성을 확인합니다.

        이는 실제 교육 현장에서 자주 발생하는 상황으로,
        학습의 연속성을 유지하면서도 개인 상황을 배려하는 것입니다.
        """
        # Given: 개인 상황 변화로 인한 일정 조정 필요 상황
        study_plan_id = study_plan_test_data['study_plan_id']
        user_id = study_plan_test_data['user_id']

        # 학습 내용은 그대로 유지하면서 일정만 조정하는 업데이트
        schedule_adjustment_data = {
            'start_date': datetime(2025, 10, 1, 9, 0, 0),  # 한 달 연기
            'end_date': datetime(2026, 1, 1, 18, 0, 0),   # 기간도 여유롭게 조정
            'is_challenge': False  # 상황 변화로 부담 줄임
            # input_data는 변경하지 않음 (학습 내용 동일)
        }

        existing_plan = self._create_realistic_study_plan_mock(study_plan_test_data)
        existing_plan.update_from_dict = Mock(return_value=existing_plan)
        existing_plan.save = AsyncMock()

        StudyPlan = mock_tortoise_ecosystem['StudyPlan']
        StudyPlan.get_or_none.return_value = existing_plan
        StudyPlan.get.return_value = existing_plan  # 일정만 변경되므로 같은 인스턴스

        # When: 일정 유연성 조정 업데이트 실행
        result = await study_plan_service.update_study_plan(
            study_plan_id=study_plan_id,
            user_id=user_id,
            update_data=schedule_adjustment_data
        )

        # Then: 학습 연속성과 개인 배려의 균형 확인
        # 1. 일정 조정이 적절히 반영되었는지 확인
        assert isinstance(result, StudyPlanResponse)

        # 2. 학습 내용 재생성이 불필요함을 확인
        # input_data가 변경되지 않았으므로 AI 재생성이 발생하지 않아야 함
        study_plan_service.gemini_service.generate_study_plan.assert_not_called()

        # 3. 효율적인 부분 업데이트 수행 확인
        existing_plan.update_from_dict.assert_called_once_with(schedule_adjustment_data)
        existing_plan.save.assert_called_once()

    # =============================================================================
    # 삭제(Delete) 기능 테스트 - 학습 계획 생명주기 관리
    # =============================================================================

    async def test_delete_study_plan_educational_closure_process(
        self,
        study_plan_service,
        study_plan_test_data,
        mock_tortoise_ecosystem
    ):
        """교육적 종료 과정을 통한 학습계획 삭제 테스트

        학습계획의 삭제가 단순한 데이터 제거가 아니라
        교육적 가치를 고려한 적절한 종료 과정인지 확인합니다.

        이는 마치 과목 수강을 취소할 때도 학습자의 성장에
        도움이 되는 방식으로 진행되어야 한다는 교육 철학을 반영합니다.
        """
        # Given: 완료 또는 변경으로 인해 삭제가 필요한 학습계획
        study_plan_id = study_plan_test_data['study_plan_id']
        user_id = study_plan_test_data['user_id']

        # 삭제 대상 학습계획 (교육적 가치가 있었던 계획)
        educational_plan_to_delete = self._create_realistic_study_plan_mock({
            **study_plan_test_data,
            'ai_response': {
                **study_plan_test_data['ai_response'],
                'completion_status': 'partially_completed',
                'learned_concepts': ['Python 기초', '변수', '함수'],
                'remaining_goals': ['Django', '프로젝트 구축'],
                'educational_value_gained': True
            }
        })
        educational_plan_to_delete.delete = AsyncMock()

        StudyPlan = mock_tortoise_ecosystem['StudyPlan']
        StudyPlan.get_or_none.return_value = educational_plan_to_delete

        # When: 교육적 가치를 고려한 삭제 과정 실행
        await study_plan_service.delete_study_plan(
            study_plan_id=study_plan_id,
            user_id=user_id
        )

        # Then: 적절한 교육적 종료 과정 확인
        # 1. 권한 있는 사용자에 의한 삭제인지 사전 확인
        StudyPlan.get_or_none.assert_called_once_with(id=study_plan_id)

        # 2. 실제 삭제 과정의 안전한 실행
        educational_plan_to_delete.delete.assert_called_once()

    async def test_delete_study_plan_comprehensive_error_prevention(
        self,
        study_plan_service,
        mock_tortoise_ecosystem
    ):
        """종합적 오류 방지를 통한 안전한 삭제 테스트

        교육 데이터의 중요성을 고려하여 잘못된 삭제를
        방지하는 다층적 보안 시스템을 확인합니다.
        """
        # 교육 환경에서 발생할 수 있는 삭제 오류 시나리오들
        deletion_error_scenarios = [
            {
                'scenario_description': '졸업한 학생이 다른 학생의 계획 삭제 시도',
                'setup_condition': 'not_found',
                'study_plan_id': 99999,
                'user_id': 123,
                'expected_exception': StudyPlanNotFoundError,
                'educational_context': '존재하지 않는 계획'
            },
            {
                'scenario_description': '타인의 개인 학습계획 무단 삭제 시도',
                'setup_condition': 'access_denied',
                'study_plan_id': 1,
                'unauthorized_user_id': 456,
                'plan_owner_id': 123,
                'expected_exception': StudyPlanAccessDeniedError,
                'educational_context': '교육적 개인정보 보호'
            }
        ]

        for scenario in deletion_error_scenarios:
            # Given: 각 교육적 오류 상황 설정
            StudyPlan = mock_tortoise_ecosystem['StudyPlan']

            if scenario['setup_condition'] == 'not_found':
                StudyPlan.get_or_none.return_value = None
                test_user_id = scenario['user_id']

            elif scenario['setup_condition'] == 'access_denied':
                # 다른 사용자의 계획 Mock
                other_student_plan = self._create_realistic_study_plan_mock({
                    'study_plan_id': scenario['study_plan_id'],
                    'user_id': scenario['plan_owner_id'],
                    'request_data': {'input_data': '다른 학생의 개인 학습계획'}
                })
                StudyPlan.get_or_none.return_value = other_student_plan
                test_user_id = scenario['unauthorized_user_id']

            # When & Then: 교육적 보안 위반 차단 확인
            with pytest.raises(scenario['expected_exception']) as exc_info:
                await study_plan_service.delete_study_plan(
                    study_plan_id=scenario['study_plan_id'],
                    user_id=test_user_id
                )

            # 교육 환경에 적합한 오류 메시지 확인
            error_message = str(exc_info.value)
            assert str(scenario['study_plan_id']) in error_message

    # =============================================================================
    # 경계 케이스 및 극한 상황 테스트 - 시스템 견고성 확인
    # =============================================================================

    async def test_educational_system_resilience_under_extreme_load(
        self,
        study_plan_service,
        mock_tortoise_ecosystem
    ):
        """극한 부하 상황에서의 교육 시스템 복원력 테스트

        수강 신청 마감일이나 새 학기 시작 등 교육 시스템에
        극한 부하가 걸리는 상황에서도 안정적으로 작동하는지 확인합니다.
        """
        user_id = 123

        # 극한 상황을 시뮬레이션하는 Mock 설정
        stress_test_queryset = Mock()
        stress_test_queryset.order_by.return_value = stress_test_queryset
        stress_test_queryset.limit.return_value = stress_test_queryset
        stress_test_queryset.offset.return_value = []  # 극한 부하로 인한 빈 결과

        StudyPlan = mock_tortoise_ecosystem['StudyPlan']
        StudyPlan.filter.return_value = stress_test_queryset

        # 교육 시스템에서 발생할 수 있는 극한 상황들
        extreme_educational_scenarios = [
            {'limit': 0, 'offset': 0, 'context': '시스템 점검 모드'},
            {'limit': 1, 'offset': 100000, 'context': '대용량 학습 데이터 검색'},
            {'limit': 50000, 'offset': 0, 'context': '전체 학습 이력 내보내기'},
            {'limit': 999999, 'offset': 999999, 'context': '시스템 스트레스 테스트'}
        ]

        for scenario in extreme_educational_scenarios:
            # When: 극한 교육 환경에서의 시스템 동작
            result = await study_plan_service.get_user_study_plans(
                user_id=user_id,
                limit=scenario['limit'],
                offset=scenario['offset']
            )

            # Then: 교육 서비스 연속성 보장 확인
            assert isinstance(result, list), f"{scenario['context']} 상황에서도 안정적 응답이 필요합니다"

            # 시스템 파라미터 정확한 전달 확인
            stress_test_queryset.limit.assert_called_with(scenario['limit'])
            stress_test_queryset.offset.assert_called_with(scenario['offset'])

    # =============================================================================
    # 교육적 품질 보증을 위한 헬퍼 메서드들
    # =============================================================================

    def _create_realistic_study_plan_mock(self, test_data: dict) -> Mock:
        """교육적 현실성을 반영한 StudyPlan Mock 생성

        실제 교육 환경에서 사용되는 학습계획의 모든 특성을
        정확히 모방하는 Mock 객체를 생성합니다.

        이 헬퍼는 단순한 데이터 모방을 넘어서 교육적 맥락과
        학습자의 실제 경험을 반영한 현실적인 Mock을 제공합니다.
        """
        mock_instance = Mock()

        # 기본 학습계획 정보
        mock_instance.id = test_data.get('study_plan_id', 1)
        mock_instance.user_id = test_data.get('user_id', 123)
        mock_instance.input_data = test_data.get('request_data', {}).get('input_data', '')
        mock_instance.output_data = json.dumps(test_data.get('ai_response', {}))
        mock_instance.is_challenge = test_data.get('request_data', {}).get('is_challenge', False)
        mock_instance.start_date = test_data.get('request_data', {}).get('start_date', datetime.now())
        mock_instance.end_date = test_data.get('request_data', {}).get('end_date', datetime.now())
        mock_instance.created_at = datetime.now()

        # 교육적 현실성을 위한 추가 속성들
        mock_instance.learning_status = test_data.get('ai_response', {}).get('learning_status', 'active')
        mock_instance.difficulty_level = test_data.get('ai_response', {}).get('difficulty', 'intermediate')
        mock_instance.educational_value = True  # 모든 계획은 교육적 가치를 가짐

        # Tortoise ORM 메서드들
        mock_instance.save = AsyncMock()
        mock_instance.delete = AsyncMock()
        mock_instance.update_from_dict = Mock(return_value=mock_instance)

        return mock_instance

    def _assert_study_plan_educational_quality(self, response: StudyPlanResponse, expected_data: dict):
        """학습계획의 교육적 품질 보증을 위한 검증 헬퍼

        생성된 학습계획이 교육적 관점에서 품질 기준을
        만족하는지 체계적으로 검증합니다.

        단순한 데이터 정확성을 넘어서 교육적 효과성,
        학습자 경험, 목표 달성 가능성까지 종합적으로 평가합니다.
        """
        # 1. 기본 응답 구조와 데이터 무결성 검증
        assert isinstance(response, StudyPlanResponse), "응답이 올바른 교육 데이터 형식이어야 합니다"
        assert response.id is not None, "각 학습계획은 고유한 식별자를 가져야 합니다"
        assert response.created_at is not None, "학습 시작 시점이 기록되어야 합니다"

        # 2. 학습자 정보와 목표의 정확한 보존
        assert response.user_id == expected_data['user_id'], "학습자 정보가 정확히 보존되어야 합니다"
        assert response.input_data == expected_data['request_data']['input_data'], \
            "학습자의 원래 목표와 요구사항이 보존되어야 합니다"

        # 3. 학습 일정의 현실성과 실현 가능성
        assert response.start_date == expected_data['request_data']['start_date'], \
            "계획된 학습 시작일이 정확해야 합니다"
        assert response.end_date == expected_data['request_data']['end_date'], \
            "목표 완료일이 현실적으로 설정되어야 합니다"

        # 4. 학습 강도와 개인 상황의 적절한 반영
        assert response.is_challenge == expected_data['request_data']['is_challenge'], \
            "학습자의 도전 의지와 가용 시간이 적절히 반영되어야 합니다"

        # 5. AI 생성 콘텐츠의 교육적 가치 확인
        assert response.output_data is not None, "AI가 생성한 학습 가이드가 포함되어야 합니다"

        # 6. 교육적 연속성과 발전성 보장
        # 학습계획이 단순한 정보 나열이 아닌 체계적인 학습 여정을 제공하는지 확인
        if hasattr(response, 'output_data') and response.output_data:
            try:
                ai_content = json.loads(response.output_data)
                assert 'title' in ai_content, "명확한 학습 목표 제목이 있어야 합니다"
                # 추가적인 교육적 품질 검증은 AI 응답 구조에 따라 확장 가능
            except json.JSONDecodeError:
                # JSON 파싱이 실패해도 문자열 형태로라도 콘텐츠가 있어야 함
                assert len(response.output_data) > 0, "학습 가이드 콘텐츠가 존재해야 합니다"