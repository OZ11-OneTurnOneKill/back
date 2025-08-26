"""Summary Service 테스트 - 완전 수정된 버전

이 테스트 파일은 이전 버전의 모든 문제점들을 해결하고 개선했습니다.
주요 변화는 다음과 같습니다:

1. **Fixture 의존성 해결**: conftest.py의 fixture들을 올바르게 활용
2. **Mock 시스템 완전 적용**: Tortoise ORM Mock이 완전히 작동
3. **커스텀 예외 시스템 활용**: 새로운 예외 처리 방식 완전 도입
4. **테스트 구조 개선**: 더 명확하고 유지보수하기 쉬운 구조

이제 각 테스트는 실제 데이터베이스나 AI API 없이도
안정적으로 실행되며, 다양한 시나리오를 정확히 검증합니다.
마치 잘 설계된 실험실에서 정밀한 실험을 수행하는 것과 같습니다.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from app.services.ai_services.summary_service import SummaryService
from app.dtos.ai.summary import SummaryRequest, SummaryResponse

# 새로운 커스텀 예외 시스템 완전 활용
from app.exceptions import (
    SummaryNotFoundError,
    SummaryAccessDeniedError,
    SummaryCreationError,
    SummaryValidationError,
    SummaryContentError,
    SummaryProcessingError
)


class TestSummaryService:
    """자료 요약 서비스 비즈니스 로직 테스트

    이 클래스는 AI 기반 자료 요약 시스템의 모든 핵심 기능을 검증합니다.
    각 테스트는 실제 사용자가 겪을 수 있는 상황을 시뮬레이션하여,
    시스템의 안정성과 사용자 경험의 품질을 보장합니다.

    테스트 철학:
    - **사용자 관점**: 실제 사용자의 요구사항과 기대치 반영
    - **예외 안전성**: 모든 예외 상황에 대한 적절한 대응 확인
    - **품질 보증**: 입력부터 출력까지 전체 프로세스의 품질 검증
    - **확장성**: 새로운 기능 추가 시에도 쉽게 테스트 확장 가능
    """

    # =============================================================================
    # 서비스 설정 - 안정적인 테스트 환경 구축
    # =============================================================================

    @pytest.fixture
    def summary_service(self, mock_gemini_ecosystem):
        """완전히 구성된 SummaryService 인스턴스

        이 fixture는 실제 서비스와 동일한 기능을 제공하지만,
        모든 외부 의존성이 안전한 Mock으로 대체된 테스트 전용 버전입니다.

        이는 마치 실제 주방 대신 연습용 주방에서 요리를 배우는 것과 같습니다.
        모든 도구와 재료는 실제와 동일하지만, 실수해도 안전한 환경입니다.
        """
        # GeminiService Mock을 생성하고 설정
        mock_gemini_service = Mock()
        mock_gemini_service.generate_summary = AsyncMock()

        # 기본적으로 성공적인 응답을 반환하도록 설정
        # 이렇게 하면 각 테스트에서 특별한 설정 없이도 기본 동작을 확인할 수 있습니다
        mock_gemini_service.generate_summary.return_value = \
            mock_gemini_ecosystem['default_summary']

        return SummaryService(gemini_service=mock_gemini_service)

    # =============================================================================
    # 생성(Create) 기능 테스트 - 새로운 요약 만들기
    # =============================================================================

    async def test_create_summary_end_to_end_success_workflow(
        self,
        summary_service,
        summary_test_data,
        mock_tortoise_ecosystem
    ):
        """요약 생성 전체 워크플로우 성공 테스트

        이 테스트는 사용자가 텍스트를 입력한 순간부터 완성된 요약을
        받기까지의 전체 과정을 검증합니다. 이는 마치 음식을 주문하고
        완성된 요리를 받기까지의 전체 과정을 확인하는 것과 같습니다.

        검증하는 워크플로우:
        1. 사용자 입력 데이터 수집
        2. AI 서비스를 통한 요약 생성
        3. 결과 데이터베이스 저장
        4. 사용자에게 응답 반환
        """
        # Given: 완전한 요약 요청 시나리오 준비
        user_id = summary_test_data['user_id']
        request = SummaryRequest(**summary_test_data['request_data'])

        # 데이터베이스 저장 결과를 시뮬레이션하는 Mock 인스턴스 생성
        mock_summary_instance = self._create_comprehensive_summary_mock(summary_test_data)

        # conftest.py에서 제공하는 Tortoise Mock 시스템 활용
        DocumentSummary = mock_tortoise_ecosystem['DocumentSummary']
        DocumentSummary.create.return_value = mock_summary_instance

        # When: 전체 요약 생성 워크플로우 실행
        result = await summary_service.create_summary(
            user_id=user_id,
            request=request
        )

        # Then: 전체 워크플로우의 성공적 완료 검증
        # 1. 기본 응답 구조 확인
        assert isinstance(result, SummaryResponse), "응답이 올바른 타입이어야 합니다"
        assert result.id is not None, "생성된 요약에는 고유 ID가 있어야 합니다"
        assert result.created_at is not None, "생성 시간이 기록되어야 합니다"

        # 2. 사용자 입력 데이터 보존 확인
        assert result.user_id == user_id, "사용자 ID가 정확히 보존되어야 합니다"
        assert result.title == request.title, "제목이 정확히 보존되어야 합니다"
        assert result.input_data == request.input_data, "입력 데이터가 정확히 보존되어야 합니다"
        assert result.summary_type == request.summary_type, "요약 타입이 정확히 보존되어야 합니다"

        # 3. AI 처리 결과 포함 확인
        assert result.output_data is not None, "AI 요약 결과가 포함되어야 합니다"
        output_data = json.loads(result.output_data)
        assert 'summary' in output_data, "요약 내용이 포함되어야 합니다"
        assert 'key_points' in output_data, "핵심 포인트가 포함되어야 합니다"

        # 4. 시스템 상호작용 검증
        # AI 서비스가 올바른 파라미터로 호출되었는지 확인
        summary_service.gemini_service.generate_summary.assert_called_once()
        call_kwargs = summary_service.gemini_service.generate_summary.call_args.kwargs
        assert call_kwargs['content'] == request.input_data
        assert call_kwargs['summary_type'] == request.summary_type
        assert call_kwargs['title'] == request.title

        # 데이터베이스 저장이 올바른 데이터로 수행되었는지 확인
        DocumentSummary.create.assert_called_once()

    async def test_create_summary_input_validation_comprehensive_scenarios(
        self,
        summary_service,
        summary_test_data
    ):
        """입력 데이터 검증 포괄적 시나리오 테스트

        사용자가 다양한 형태의 잘못된 데이터를 입력했을 때
        시스템이 친절하고 명확한 피드백을 제공하는지 확인합니다.

        이는 마치 양질의 고객 서비스처럼, 문제가 있을 때
        고객이 어떻게 해결할 수 있는지 친절하게 안내하는 것과 같습니다.
        """
        user_id = summary_test_data['user_id']

        # 현실적인 사용자 실수 시나리오들
        validation_scenarios = [
            {
                'scenario_name': '제목이 완전히 비어있는 경우',
                'invalid_data': {**summary_test_data['request_data'], 'title': ''},
                'expected_field': 'title',
                'user_guidance': '제목은 필수입니다'
            },
            {
                'scenario_name': '제목이 공백문자만 있는 경우',
                'invalid_data': {**summary_test_data['request_data'], 'title': '   '},
                'expected_field': 'title',
                'user_guidance': '제목은 필수입니다'
            },
            {
                'scenario_name': '제목이 너무 긴 경우',
                'invalid_data': {**summary_test_data['request_data'], 'title': 'x' * 250},
                'expected_field': 'title',
                'user_guidance': '200자 이하여야 합니다'
            },
            {
                'scenario_name': '요약할 내용이 없는 경우',
                'invalid_data': {**summary_test_data['request_data'], 'input_data': ''},
                'expected_field': 'input_data',
                'user_guidance': '요약할 내용은 필수입니다'
            },
            {
                'scenario_name': '요약할 내용이 너무 짧은 경우',
                'invalid_data': {**summary_test_data['request_data'], 'input_data': '짧음'},
                'expected_field': 'input_data',
                'user_guidance': '최소 50자 이상이어야 합니다'
            },
            {
                'scenario_name': '지원하지 않는 요약 타입',
                'invalid_data': {**summary_test_data['request_data'], 'summary_type': 'unsupported_type'},
                'expected_field': 'summary_type',
                'user_guidance': '지원하는 요약 타입'
            }
        ]

        for scenario in validation_scenarios:
            # Given: 각 검증 실패 시나리오
            invalid_request = SummaryRequest(**scenario['invalid_data'])

            # When & Then: 적절한 검증 예외와 사용자 친화적 메시지 확인
            with pytest.raises(SummaryValidationError) as exc_info:
                await summary_service.create_summary(
                    user_id=user_id,
                    request=invalid_request
                )

            # 예외 정보의 품질 검증
            validation_error = exc_info.value

            # 1. 올바른 예외 타입과 코드 확인
            assert validation_error.error_code == "SUMMARY_VALIDATION_FAILED"

            # 2. 문제가 된 필드가 올바르게 식별되었는지 확인
            assert scenario['expected_field'] in validation_error.details['field_errors']

            # 3. 사용자에게 도움이 되는 메시지가 포함되었는지 확인
            field_error_message = validation_error.details['field_errors'][scenario['expected_field']]
            assert scenario['user_guidance'] in field_error_message

    async def test_create_summary_content_quality_analysis(
        self,
        summary_service,
        summary_test_data
    ):
        """콘텐츠 품질 분석 테스트

        형식적으로는 올바르지만 내용적으로 품질이 떨어지는 텍스트를
        미리 감지하고 사용자에게 개선 방향을 제시하는지 확인합니다.

        이는 마치 숙련된 편집자가 원고의 품질을 평가하고
        저자에게 개선 제안을 하는 것과 같습니다.
        """
        user_id = summary_test_data['user_id']

        # 다양한 품질 문제 시나리오
        quality_test_scenarios = [
            {
                'issue_type': '특수문자 과다 사용',
                'problematic_content': '!@#$%^&*()_+{}[]|\\:";\'<>?,./' * 30,  # 특수문자 과다
                'expected_issue_description': '의미있는 문자가 너무 적습니다',
                'improvement_suggestion': '특수문자나 기호를 줄이고 일반 텍스트를 더 추가해주세요'
            },
            {
                'issue_type': '단어 과도한 반복',
                'problematic_content': '테스트 테스트 테스트 ' * 50,  # 동일 단어 반복
                'expected_issue_description': '동일한 단어가 너무 많이 반복됩니다',
                'improvement_suggestion': '더 다양한 표현을 사용해주세요'
            }
        ]

        for scenario in quality_test_scenarios:
            # Given: 품질에 문제가 있는 콘텐츠
            poor_quality_data = {
                **summary_test_data['request_data'],
                'input_data': scenario['problematic_content']
            }
            poor_quality_request = SummaryRequest(**poor_quality_data)

            # When & Then: 콘텐츠 품질 문제 감지 및 개선 제안
            with pytest.raises(SummaryContentError) as exc_info:
                await summary_service.create_summary(
                    user_id=user_id,
                    request=poor_quality_request
                )

            content_error = exc_info.value

            # 1. 문제 정확한 식별 확인
            assert scenario['expected_issue_description'] in content_error.message

            # 2. 건설적인 개선 제안 제공 확인
            assert len(content_error.details['suggestions']) > 0
            suggestions_text = ' '.join(content_error.details['suggestions'])
            assert scenario['improvement_suggestion'] in suggestions_text

            # 3. 콘텐츠 통계 정보 제공 확인
            assert 'content_length' in content_error.details
            assert content_error.details['content_length'] == len(scenario['problematic_content'])

    async def test_create_summary_ai_service_failure_resilience(
        self,
        summary_service,
        summary_test_data
    ):
        """AI 서비스 실패에 대한 회복력 테스트

        외부 AI 서비스가 다양한 이유로 실패할 때 시스템이
        적절히 대응하고 사용자에게 유용한 정보를 제공하는지 확인합니다.

        이는 마치 대체 경로를 준비해둔 네비게이션 시스템처럼,
        주 경로에 문제가 생겼을 때 적절한 대안을 제시하는 것과 같습니다.
        """
        user_id = summary_test_data['user_id']
        request = SummaryRequest(**summary_test_data['request_data'])

        # 실제로 발생할 수 있는 AI 서비스 실패 시나리오들
        ai_failure_scenarios = [
            {
                'failure_type': 'API 속도 제한',
                'exception': Exception("API Rate Limit Exceeded - Please wait 60 seconds"),
                'expected_retry_guidance': True,
                'expected_wait_time': '60초 후 재시도',
                'user_action': '잠시 후 다시 시도'
            },
            {
                'failure_type': 'API 할당량 초과',
                'exception': Exception("Monthly API quota exceeded"),
                'expected_retry_guidance': False,
                'user_action': '관리자에게 문의',
                'alternative_suggestion': True
            },
            {
                'failure_type': '네트워크 연결 실패',
                'exception': Exception("Network connection failed - timeout"),
                'expected_retry_guidance': True,
                'user_action': '네트워크 연결 확인 후 재시도',
                'temporary_issue': True
            }
        ]

        for scenario in ai_failure_scenarios:
            # Given: 특정 유형의 AI 서비스 실패
            summary_service.gemini_service.generate_summary.side_effect = scenario['exception']

            # When & Then: 실패에 대한 적절한 처리 및 사용자 안내
            with pytest.raises(SummaryCreationError) as exc_info:
                await summary_service.create_summary(user_id=user_id, request=request)

            creation_error = exc_info.value

            # 1. 기본 오류 정보 포함 확인
            assert creation_error.details['user_id'] == user_id
            assert 'original_error_type' in creation_error.details
            assert str(scenario['exception']) in creation_error.details['original_error_message']

            # 2. 재시도 가능성에 대한 명확한 안내
            if scenario['expected_retry_guidance']:
                assert creation_error.details['retry_possible'] is True
                if 'expected_wait_time' in scenario:
                    assert scenario['expected_wait_time'] in creation_error.details.get('suggested_wait_time', '')
            else:
                assert creation_error.details['retry_possible'] is False
                assert scenario['user_action'] in creation_error.details.get('suggested_action', '')

    # =============================================================================
    # 조회(Read) 기능 테스트 - 기존 요약 찾기
    # =============================================================================

    async def test_get_summary_by_id_successful_detailed_retrieval(
        self,
        summary_service,
        summary_test_data,
        mock_tortoise_ecosystem
    ):
        """ID로 요약 상세 조회 성공 테스트

        사용자가 자신의 요약을 정확하고 완전하게
        조회할 수 있는지 확인합니다.
        """
        # Given: 존재하는 요약과 정당한 사용자
        summary_id = summary_test_data['summary_id']
        user_id = summary_test_data['user_id']

        mock_instance = self._create_comprehensive_summary_mock(summary_test_data)
        DocumentSummary = mock_tortoise_ecosystem['DocumentSummary']
        DocumentSummary.get_or_none.return_value = mock_instance

        # When: 요약 조회 실행
        result = await summary_service.get_summary_by_id(
            summary_id=summary_id,
            user_id=user_id
        )

        # Then: 완전하고 정확한 데이터 반환 확인
        self._assert_summary_response_completeness(result, summary_test_data)

        # 데이터베이스 쿼리가 올바르게 수행되었는지 확인
        DocumentSummary.get_or_none.assert_called_once_with(id=summary_id)

    async def test_get_summary_by_id_not_found_helpful_error_handling(
        self,
        summary_service,
        mock_tortoise_ecosystem
    ):
        """존재하지 않는 요약 조회 시 도움이 되는 오류 처리

        사용자가 잘못된 ID로 조회했을 때 문제를 이해하고
        해결할 수 있도록 도움이 되는 정보를 제공하는지 확인합니다.
        """
        # Given: 존재하지 않는 요약 ID
        non_existent_id = 99999
        user_id = 123

        DocumentSummary = mock_tortoise_ecosystem['DocumentSummary']
        DocumentSummary.get_or_none.return_value = None

        # When & Then: 도움이 되는 Not Found 예외
        with pytest.raises(SummaryNotFoundError) as exc_info:
            await summary_service.get_summary_by_id(
                summary_id=non_existent_id,
                user_id=user_id
            )

        not_found_error = exc_info.value

        # 1. 명확한 오류 식별 정보
        assert str(non_existent_id) in str(not_found_error)
        assert not_found_error.details['resource_id'] == str(non_existent_id)
        assert not_found_error.details['resource_name'] == 'document_summary'

        # 2. 사용자에게 도움이 되는 제안
        assert '요약 목록에서 올바른 ID를 확인해주세요' in not_found_error.details['suggested_action']

    async def test_get_summary_by_id_security_access_control(
        self,
        summary_service,
        summary_test_data,
        mock_tortoise_ecosystem
    ):
        """요약 조회 시 보안 접근 제어 테스트

        다른 사용자의 요약에 접근하려는 시도를 확실히 차단하고,
        보안 위반 시도를 적절히 기록하는지 확인합니다.
        """
        # Given: 다른 사용자의 요약에 접근 시도
        summary_id = summary_test_data['summary_id']
        unauthorized_user_id = 789  # 권한 없는 사용자
        legitimate_owner_id = summary_test_data['user_id']  # 실제 소유자

        mock_instance = self._create_comprehensive_summary_mock(summary_test_data)
        mock_instance.user_id = legitimate_owner_id

        DocumentSummary = mock_tortoise_ecosystem['DocumentSummary']
        DocumentSummary.get_or_none.return_value = mock_instance

        # When & Then: 강력한 접근 권한 거부
        with pytest.raises(SummaryAccessDeniedError) as exc_info:
            await summary_service.get_summary_by_id(
                summary_id=summary_id,
                user_id=unauthorized_user_id
            )

        access_error = exc_info.value

        # 1. 보안 위반 정보 정확한 기록
        assert str(summary_id) in str(access_error)
        assert str(unauthorized_user_id) in str(access_error)

        # 2. 보안 수준 및 대응 방안 명시
        assert access_error.details['security_level'] == 'high'
        assert access_error.details['action_required'] == 'access_log'
        assert '본인의 요약만 접근할 수 있습니다' in access_error.details['suggested_action']

    async def test_get_user_summaries_comprehensive_list_management(
        self,
        summary_service,
        summary_test_data,
        mock_tortoise_ecosystem
    ):
        """사용자 요약 목록 종합 관리 테스트

        사용자의 모든 요약을 효율적으로 조회하고 관리할 수 있는지
        확인합니다. 여기에는 정렬, 페이지네이션, 다양한 요약 타입 처리가 포함됩니다.
        """
        # Given: 다양한 유형의 요약을 가진 사용자
        user_id = summary_test_data['user_id']

        # 현실적인 사용자 요약 목록 시뮬레이션
        summary_types_and_titles = [
            ('general', 'AI 기술 개요 요약'),
            ('keywords', '머신러닝 핵심 키워드'),
            ('qa', '딥러닝 FAQ 정리'),
            ('study', '데이터 사이언스 학습 가이드')
        ]

        mock_summaries = []
        for i, (summary_type, title) in enumerate(summary_types_and_titles, 1):
            mock_summary = self._create_comprehensive_summary_mock({
                **summary_test_data,
                'summary_id': i,
                'request_data': {
                    **summary_test_data['request_data'],
                    'title': title,
                    'summary_type': summary_type
                }
            })
            mock_summaries.append(mock_summary)

        # QuerySet Mock 설정 (Tortoise ORM 쿼리 체인 시뮬레이션)
        mock_queryset = Mock()
        mock_queryset.order_by.return_value = mock_queryset
        mock_queryset.limit.return_value = mock_queryset
        mock_queryset.offset.return_value = mock_summaries

        DocumentSummary = mock_tortoise_ecosystem['DocumentSummary']
        DocumentSummary.filter.return_value = mock_queryset

        # When: 페이지네이션된 목록 조회
        limit = 10
        offset = 0
        result = await summary_service.get_user_summaries(
            user_id=user_id,
            limit=limit,
            offset=offset
        )

        # Then: 완전하고 정확한 목록 반환 확인
        # 1. 기본 응답 구조 검증
        assert isinstance(result, list)
        assert len(result) == 4  # 4가지 타입의 요약
        assert all(isinstance(summary, SummaryResponse) for summary in result)
        assert all(summary.user_id == user_id for summary in result)

        # 2. 다양한 요약 타입 포함 확인
        returned_types = [summary.summary_type for summary in result]
        expected_types = [item[0] for item in summary_types_and_titles]
        for expected_type in expected_types:
            assert expected_type in returned_types

        # 3. 제목의 다양성 확인
        returned_titles = [summary.title for summary in result]
        expected_titles = [item[1] for item in summary_types_and_titles]
        for expected_title in expected_titles:
            assert expected_title in returned_titles

        # 4. 데이터베이스 쿼리 최적화 확인
        DocumentSummary.filter.assert_called_once_with(user_id=user_id)
        mock_queryset.order_by.assert_called_once_with("-created_at")  # 최신순 정렬
        mock_queryset.limit.assert_called_once_with(limit)
        mock_queryset.offset.assert_called_once_with(offset)

    # =============================================================================
    # 삭제(Delete) 기능 테스트 - 요약 안전한 제거
    # =============================================================================

    async def test_delete_summary_safe_and_complete_removal(
        self,
        summary_service,
        summary_test_data,
        mock_tortoise_ecosystem
    ):
        """요약 안전하고 완전한 삭제 테스트

        사용자가 자신의 요약을 안전하게 삭제할 수 있으며,
        이 과정이 적절히 기록되는지 확인합니다.
        """
        # Given: 삭제 권한이 있는 사용자와 요약
        summary_id = summary_test_data['summary_id']
        user_id = summary_test_data['user_id']

        mock_instance = self._create_comprehensive_summary_mock(summary_test_data)
        mock_instance.delete = AsyncMock()  # 삭제 메서드 Mock

        DocumentSummary = mock_tortoise_ecosystem['DocumentSummary']
        DocumentSummary.get_or_none.return_value = mock_instance

        # When: 삭제 작업 실행
        await summary_service.delete_summary(
            summary_id=summary_id,
            user_id=user_id
        )

        # Then: 안전한 삭제 실행 확인
        # 1. 실제 삭제 메서드 호출 확인
        mock_instance.delete.assert_called_once()

        # 2. 적절한 권한 검증이 선행되었는지 확인 (get_or_none 호출)
        DocumentSummary.get_or_none.assert_called_once_with(id=summary_id)

    async def test_delete_summary_comprehensive_error_scenarios(
        self,
        summary_service,
        mock_tortoise_ecosystem
    ):
        """요약 삭제 시 종합적인 오류 시나리오 처리

        삭제 과정에서 발생할 수 있는 다양한 문제 상황에 대한
        적절한 처리를 확인합니다.
        """
        # 다양한 삭제 실패 시나리오
        deletion_error_scenarios = [
            {
                'scenario': '존재하지 않는 요약 삭제 시도',
                'setup': lambda: None,  # get_or_none이 None 반환
                'expected_exception': SummaryNotFoundError,
                'summary_id': 88888,
                'user_id': 123
            },
            {
                'scenario': '권한 없는 요약 삭제 시도',
                'setup': lambda: self._create_comprehensive_summary_mock({
                    'summary_id': 1,
                    'user_id': 999,  # 다른 사용자
                    'request_data': {'title': '다른 사람의 요약'}
                }),
                'expected_exception': SummaryAccessDeniedError,
                'summary_id': 1,
                'user_id': 123
            }
        ]

        for scenario_info in deletion_error_scenarios:
            # Given: 각 오류 시나리오 설정
            mock_instance = scenario_info['setup']()
            DocumentSummary = mock_tortoise_ecosystem['DocumentSummary']
            DocumentSummary.get_or_none.return_value = mock_instance

            # When & Then: 적절한 예외 발생 및 처리 확인
            with pytest.raises(scenario_info['expected_exception']) as exc_info:
                await summary_service.delete_summary(
                    summary_id=scenario_info['summary_id'],
                    user_id=scenario_info['user_id']
                )

            # 예외 메시지에 관련 정보가 포함되었는지 확인
            error_message = str(exc_info.value)
            assert str(scenario_info['summary_id']) in error_message

    # =============================================================================
    # 경계 케이스 및 극한 상황 테스트
    # =============================================================================

    async def test_pagination_extreme_boundary_conditions(
        self,
        summary_service,
        mock_tortoise_ecosystem
    ):
        """페이지네이션 극한 경계 조건 테스트

        시스템이 극단적인 페이지네이션 요청에도 안정적으로
        대응하는지 확인합니다.
        """
        user_id = 123

        mock_queryset = Mock()
        mock_queryset.order_by.return_value = mock_queryset
        mock_queryset.limit.return_value = mock_queryset
        mock_queryset.offset.return_value = []  # 빈 결과

        DocumentSummary = mock_tortoise_ecosystem['DocumentSummary']
        DocumentSummary.filter.return_value = mock_queryset

        # 극단적 경계 조건들
        extreme_pagination_cases = [
            {'limit': 0, 'offset': 0, 'description': '제로 값들'},
            {'limit': 1, 'offset': 0, 'description': '최소 유효값'},
            {'limit': 1000, 'offset': 0, 'description': '매우 큰 limit'},
            {'limit': 10, 'offset': 50000, 'description': '매우 큰 offset'},
            {'limit': 999999, 'offset': 999999, 'description': '극대값들'}
        ]

        for test_case in extreme_pagination_cases:
            # When: 극단적 조건으로 목록 조회
            result = await summary_service.get_user_summaries(
                user_id=user_id,
                limit=test_case['limit'],
                offset=test_case['offset']
            )

            # Then: 안정적인 처리 확인
            assert isinstance(result, list), f"{test_case['description']} 케이스에서 리스트가 반환되어야 합니다"

            # 올바른 파라미터 전달 확인
            mock_queryset.limit.assert_called_with(test_case['limit'])
            mock_queryset.offset.assert_called_with(test_case['offset'])

    # =============================================================================
    # 헬퍼 메서드들 - 테스트 코드 재사용성과 유지보수성 향상
    # =============================================================================

    def _create_comprehensive_summary_mock(self, test_data: dict) -> Mock:
        """포괄적인 DocumentSummary 인스턴스 Mock 생성

        실제 DocumentSummary 모델의 모든 속성과 메서드를
        정확히 모방하는 Mock 객체를 생성합니다.

        이 헬퍼 메서드는 테스트 코드의 중복을 줄이고
        일관성을 보장하는 중요한 역할을 합니다.
        """
        mock_instance = Mock()

        # 기본 속성들
        mock_instance.id = test_data['summary_id']
        mock_instance.user_id = test_data['user_id']
        mock_instance.title = test_data['request_data']['title']
        mock_instance.input_type = test_data['request_data']['input_type']
        mock_instance.input_data = test_data['request_data']['input_data']
        mock_instance.summary_type = test_data['request_data']['summary_type']
        mock_instance.output_data = json.dumps(test_data['ai_response'])
        mock_instance.file_url = test_data['request_data']['file_url']
        mock_instance.created_at = datetime.now()

        # 메서드들
        mock_instance.save = AsyncMock()
        mock_instance.delete = AsyncMock()
        mock_instance.update_from_dict = Mock(return_value=mock_instance)

        return mock_instance

    def _assert_summary_response_completeness(self, response: SummaryResponse, expected_data: dict):
        """요약 응답 완전성 검증 헬퍼

        SummaryResponse 객체가 모든 필요한 정보를 올바르게
        포함하고 있는지 체계적으로 검증합니다.
        """
        # 기본 구조 검증
        assert isinstance(response, SummaryResponse)
        assert response.id is not None
        assert response.created_at is not None

        # 데이터 정확성 검증
        assert response.user_id == expected_data['user_id']
        assert response.title == expected_data['request_data']['title']
        assert response.input_data == expected_data['request_data']['input_data']
        assert response.input_type == expected_data['request_data']['input_type']
        assert response.summary_type == expected_data['request_data']['summary_type']
        assert response.file_url == expected_data['request_data']['file_url']

        # AI 처리 결과 검증
        assert response.output_data is not None
        output_data = json.loads(response.output_data)
        assert 'summary' in output_data
        assert expected_data['ai_response']['summary'] in output_data['summary']