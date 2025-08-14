"""테스트 환경 통합 설정

이 파일은 모든 테스트에서 공통으로 사용할 설정들을 정의합니다.
마치 건물의 기초와 같이, 안정적이고 일관된 테스트 환경을 제공합니다.

설계 원칙:
1. DRY (Don't Repeat Yourself) - 중복 제거
2. 일관성 - 모든 테스트에서 동일한 방식 사용  
3. 확장성 - 새로운 테스트 추가 시 쉽게 확장 가능
4. 격리성 - 각 테스트는 독립적으로 실행
"""

import pytest
import sys
import json
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List


# =============================================================================
# Tortoise ORM 완전 Mock 설정
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def mock_tortoise_ecosystem():
    """Tortoise ORM 생태계를 완전히 Mock으로 교체

    이 fixture는 세션 전체에 걸쳐 자동으로 적용되어
    모든 데이터베이스 의존성을 제거합니다.

    마치 연극 무대에서 실제 건물 대신 세트를 사용하는 것처럼,
    실제 데이터베이스 대신 가상의 환경을 제공합니다.
    """

    # 1. StudyPlan 모델 Mock 생성
    mock_study_plan_class = create_model_mock('StudyPlan')

    # 2. DocumentSummary 모델 Mock 생성  
    mock_document_summary_class = create_model_mock('DocumentSummary')

    # 3. 모델 모듈들을 sys.modules에 등록
    mock_ai_models = MagicMock()
    mock_ai_models.StudyPlan = mock_study_plan_class
    mock_ai_models.DocumentSummary = mock_document_summary_class

    # 여러 경로로 접근 가능하도록 등록
    paths_to_mock = [
        'app.models.ai',
        'app.models.study_plan',
        'app.models.summary',
        'app.models'
    ]

    for path in paths_to_mock:
        sys.modules[path] = mock_ai_models

    # 4. Tortoise ORM 핵심 모듈들도 Mock
    mock_tortoise_modules = {
        'tortoise': create_tortoise_mock(),
        'tortoise.models': MagicMock(),
        'tortoise.fields': MagicMock(),
        'tortoise.exceptions': MagicMock(),
        'tortoise.transactions': MagicMock()
    }

    for module_path, mock_module in mock_tortoise_modules.items():
        sys.modules[module_path] = mock_module

    yield {
        'StudyPlan': mock_study_plan_class,
        'DocumentSummary': mock_document_summary_class,
        'tortoise': mock_tortoise_modules['tortoise']
    }


def create_model_mock(model_name: str) -> MagicMock:
    """Tortoise ORM 모델의 완전한 Mock을 생성

    Args:
        model_name: 모델 클래스 이름

    Returns:
        완전히 Mock된 모델 클래스

    이 함수는 실제 Tortoise ORM 모델의 모든 주요 메서드를
    Mock으로 대체합니다. 마치 실제 배우 대신 스턴트맨을
    사용하는 것과 같은 개념입니다.
    """
    mock_class = MagicMock()
    mock_class.__name__ = model_name

    # CRUD 메서드들 설정
    mock_class.create = AsyncMock()
    mock_class.get = AsyncMock()
    mock_class.get_or_none = AsyncMock()
    mock_class.filter = Mock()
    mock_class.all = Mock()
    mock_class.delete = AsyncMock()
    mock_class.update = AsyncMock()
    mock_class.bulk_create = AsyncMock()

    # QuerySet 메서드들을 지원하는 Mock 생성
    def create_queryset_mock():
        queryset = Mock()
        queryset.order_by = Mock(return_value=queryset)
        queryset.limit = Mock(return_value=queryset)
        queryset.offset = Mock(return_value=queryset)
        queryset.filter = Mock(return_value=queryset)
        queryset.exclude = Mock(return_value=queryset)
        queryset.count = AsyncMock(return_value=0)
        return queryset

    # filter 메서드가 QuerySet을 반환하도록 설정
    mock_class.filter.return_value = create_queryset_mock()
    mock_class.all.return_value = create_queryset_mock()

    return mock_class


def create_tortoise_mock() -> MagicMock:
    """Tortoise ORM 메인 모듈 Mock 생성"""
    mock_tortoise = MagicMock()
    mock_tortoise.init = AsyncMock()
    mock_tortoise.close_connections = AsyncMock()
    mock_tortoise.generate_schemas = AsyncMock()
    mock_tortoise.Tortoise = MagicMock()

    # 트랜잭션 관련 Mock
    mock_transaction = MagicMock()
    mock_transaction.__aenter__ = AsyncMock()
    mock_transaction.__aexit__ = AsyncMock()
    mock_tortoise.transactions.in_transaction.return_value = mock_transaction

    return mock_tortoise


# =============================================================================
# Gemini API Mock 설정
# =============================================================================

@pytest.fixture
def mock_gemini_ecosystem():
    """Gemini API 생태계를 완전히 Mock으로 설정

    외부 AI API 호출을 모두 차단하고 예측 가능한 응답을 제공합니다.
    마치 실제 요리사 대신 요리 로봇을 사용하는 것과 같습니다.
    """
    with patch('app.services.ai_services.gemini_service.genai') as mock_genai:
        # 기본 Mock 설정
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = Mock()

        # 다양한 응답 시나리오를 지원하는 응답 생성기
        def create_mock_response(content: str):
            mock_response = Mock()
            mock_response.text = content
            return mock_response

        # 기본 성공 응답 설정
        default_study_plan_response = {
            "title": "테스트 학습계획",
            "total_weeks": 4,
            "difficulty": "beginner",
            "weekly_plans": [
                {
                    "week": 1,
                    "title": "기초 학습",
                    "topics": ["기본 개념"],
                    "goals": ["이해하기"],
                    "estimated_hours": 10
                }
            ],
            "milestones": [{"week": 4, "milestone": "완료"}]
        }

        default_summary_response = {
            "title": "테스트 요약",
            "summary_type": "general",
            "summary": "테스트 요약 내용입니다.",
            "key_points": ["포인트 1", "포인트 2"],
            "word_count": 100,
            "summary_ratio": "50%"
        }

        mock_model.generate_content_async = AsyncMock(
            return_value=create_mock_response(json.dumps(default_study_plan_response))
        )

        yield {
            'genai': mock_genai,
            'model': mock_model,
            'create_response': create_mock_response,
            'default_study_plan': default_study_plan_response,
            'default_summary': default_summary_response
        }


# =============================================================================
# 공통 Test Data Fixtures
# =============================================================================

@pytest.fixture
def study_plan_test_data():
    """학습계획 테스트용 데이터 세트

    실제 사용자 시나리오를 반영한 다양한 테스트 데이터를 제공합니다.
    마치 요리책에 있는 재료 목록과 같은 역할을 합니다.
    """
    return {
        'user_id': 123,
        'study_plan_id': 1,
        'request_data': {
            'input_data': "Python 웹 개발 3개월 마스터 과정",
            'start_date': datetime(2025, 8, 15, 9, 0, 0),
            'end_date': datetime(2025, 11, 15, 18, 0, 0),
            'is_challenge': False
        },
        'ai_response': {
            "title": "Python 웹 개발 완성 로드맵",
            "total_weeks": 12,
            "difficulty": "beginner_to_intermediate",
            "weekly_plans": [
                {
                    "week": 1,
                    "title": "Python 기초 문법 마스터",
                    "topics": ["변수와 데이터 타입", "제어문", "함수"],
                    "goals": ["기본 문법 완전 이해", "간단한 프로그램 작성"],
                    "estimated_hours": 15
                },
                {
                    "week": 2,
                    "title": "객체지향 프로그래밍",
                    "topics": ["클래스와 객체", "상속", "다형성"],
                    "goals": ["OOP 개념 이해", "클래스 설계 연습"],
                    "estimated_hours": 18
                }
            ],
            "milestones": [
                {"week": 4, "milestone": "Python 기초 완료"},
                {"week": 8, "milestone": "Django 기본 완료"},
                {"week": 12, "milestone": "프로젝트 완성"}
            ]
        },
        'update_data': {
            'input_data': "수정된 Python 풀스택 개발 과정",
            'start_date': datetime(2025, 9, 1, 9, 0, 0)
        }
    }


@pytest.fixture
def summary_test_data():
    """요약 테스트용 데이터 세트"""
    return {
        'user_id': 456,
        'summary_id': 2,
        'request_data': {
            'title': "인공지능과 머신러닝 핵심 개념",
            'input_data': "인공지능(AI)은 컴퓨터 시스템이 인간과 같은 지능적 행동을 수행할 수 있게 하는 기술입니다. 머신러닝은 AI의 하위 분야로, 명시적으로 프로그래밍하지 않고도 데이터에서 학습할 수 있는 능력을 컴퓨터에 부여합니다. 딥러닝은 인공 신경망을 사용하는 머신러닝의 특별한 형태입니다.",
            'input_type': 'text',
            'summary_type': 'general',
            'file_url': None
        },
        'ai_response': {
            "title": "인공지능과 머신러닝 핵심 개념",
            "summary_type": "general",
            "summary": "AI는 컴퓨터가 인간과 같은 지능을 구현하는 기술이며, 머신러닝은 데이터에서 자동으로 학습하는 AI의 하위 분야입니다. 딥러닝은 신경망을 활용하는 고급 머신러닝 기법입니다.",
            "key_points": [
                "AI는 인간과 같은 지능적 행동을 구현",
                "머신러닝은 데이터에서 자동 학습",
                "딥러닝은 신경망 기반 기술",
                "머신러닝은 AI의 하위 분야"
            ],
            "word_count": 180,
            "summary_ratio": "35%"
        }
    }


# =============================================================================
# 서비스 Mock Fixtures  
# =============================================================================

@pytest.fixture
def mock_study_plan_service(study_plan_test_data):
    """완전히 Mock된 StudyPlanService

    실제 서비스 대신 예측 가능한 동작을 하는 Mock을 제공합니다.
    이를 통해 외부 의존성 없이 비즈니스 로직을 테스트할 수 있습니다.
    """
    service = Mock()

    # 각 메서드를 AsyncMock으로 설정
    service.create_study_plan = AsyncMock()
    service.get_study_plan_by_id = AsyncMock()
    service.get_user_study_plans = AsyncMock()
    service.update_study_plan = AsyncMock()
    service.delete_study_plan = AsyncMock()

    # 기본 응답 데이터 설정
    mock_response = create_study_plan_response_mock(study_plan_test_data)
    service.create_study_plan.return_value = mock_response
    service.get_study_plan_by_id.return_value = mock_response
    service.get_user_study_plans.return_value = [mock_response]
    service.update_study_plan.return_value = mock_response

    return service


@pytest.fixture
def mock_summary_service(summary_test_data):
    """완전히 Mock된 SummaryService"""
    service = Mock()

    service.create_summary = AsyncMock()
    service.get_summary_by_id = AsyncMock()
    service.get_user_summaries = AsyncMock()
    service.delete_summary = AsyncMock()

    # 기본 응답 데이터 설정
    mock_response = create_summary_response_mock(summary_test_data)
    service.create_summary.return_value = mock_response
    service.get_summary_by_id.return_value = mock_response
    service.get_user_summaries.return_value = [mock_response]

    return service


# =============================================================================
# Response Mock 생성 헬퍼들
# =============================================================================

def create_study_plan_response_mock(test_data: Dict[str, Any]) -> Mock:
    """StudyPlanResponse Mock 생성

    실제 응답 객체와 동일한 인터페이스를 가진 Mock을 생성합니다.
    """
    mock_response = Mock()
    mock_response.id = test_data['study_plan_id']
    mock_response.user_id = test_data['user_id']
    mock_response.input_data = test_data['request_data']['input_data']
    mock_response.output_data = json.dumps(test_data['ai_response'])
    mock_response.is_challenge = test_data['request_data']['is_challenge']
    mock_response.start_date = test_data['request_data']['start_date']
    mock_response.end_date = test_data['request_data']['end_date']
    mock_response.created_at = datetime.now()

    # dict() 메서드 지원
    mock_response.dict.return_value = {
        'id': mock_response.id,
        'user_id': mock_response.user_id,
        'input_data': mock_response.input_data,
        'output_data': mock_response.output_data,
        'is_challenge': mock_response.is_challenge,
        'start_date': mock_response.start_date.isoformat(),
        'end_date': mock_response.end_date.isoformat(),
        'created_at': mock_response.created_at.isoformat()
    }

    return mock_response


def create_summary_response_mock(test_data: Dict[str, Any]) -> Mock:
    """SummaryResponse Mock 생성"""
    mock_response = Mock()
    mock_response.id = test_data['summary_id']
    mock_response.user_id = test_data['user_id']
    mock_response.title = test_data['request_data']['title']
    mock_response.input_type = test_data['request_data']['input_type']
    mock_response.input_data = test_data['request_data']['input_data']
    mock_response.summary_type = test_data['request_data']['summary_type']
    mock_response.output_data = json.dumps(test_data['ai_response'])
    mock_response.file_url = test_data['request_data']['file_url']
    mock_response.created_at = datetime.now()

    mock_response.dict.return_value = {
        'id': mock_response.id,
        'user_id': mock_response.user_id,
        'title': mock_response.title,
        'input_type': mock_response.input_type,
        'input_data': mock_response.input_data,
        'summary_type': mock_response.summary_type,
        'output_data': mock_response.output_data,
        'file_url': mock_response.file_url,
        'created_at': mock_response.created_at.isoformat()
    }

    return mock_response


# =============================================================================
# 테스트 유틸리티 함수들
# =============================================================================

def assert_study_plan_response_valid(response, expected_data: Dict[str, Any]):
    """StudyPlan 응답 검증을 위한 헬퍼 함수

    반복적인 검증 로직을 캡슐화하여 테스트 코드의 가독성을 높입니다.
    """
    assert response.id == expected_data['study_plan_id']
    assert response.user_id == expected_data['user_id']
    assert response.input_data == expected_data['request_data']['input_data']
    assert response.is_challenge == expected_data['request_data']['is_challenge']


def assert_summary_response_valid(response, expected_data: Dict[str, Any]):
    """Summary 응답 검증을 위한 헬퍼 함수"""
    assert response.id == expected_data['summary_id']
    assert response.user_id == expected_data['user_id']
    assert response.title == expected_data['request_data']['title']
    assert response.summary_type == expected_data['request_data']['summary_type']


# =============================================================================
# 에러 시나리오 테스트 지원
# =============================================================================

@pytest.fixture
def error_scenarios():
    """다양한 에러 시나리오를 위한 데이터

    예외 상황 테스트를 체계적으로 수행할 수 있도록 도와줍니다.
    """
    return {
        'not_found': {
            'study_plan_id': 999,
            'summary_id': 999,
            'user_id': 123
        },
        'access_denied': {
            'study_plan_id': 1,
            'summary_id': 1,
            'owner_user_id': 123,
            'other_user_id': 456
        },
        'api_errors': {
            'rate_limit': "API Rate Limit Exceeded",
            'network_error': "Network Connection Failed",
            'invalid_response': "Invalid JSON response",
            'timeout': "Request Timeout"
        },
        'validation_errors': {
            'empty_input': "",
            'too_short': "짧음",
            'too_long': "x" * 60000,
            'invalid_type': 123
        }
    }


# =============================================================================
# 로깅 및 성능 측정
# =============================================================================

@pytest.fixture(autouse=True)
def configure_test_environment():
    """테스트 환경 전반적인 설정

    로깅 레벨 조정, 경고 메시지 억제 등을 수행합니다.
    """
    import logging
    import warnings

    # 테스트 중 불필요한 로그 메시지 최소화
    logging.getLogger().setLevel(logging.WARNING)
    logging.getLogger('app').setLevel(logging.ERROR)

    # DeprecationWarning 등 테스트와 무관한 경고 억제
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

    yield

    # 테스트 완료 후 정리 작업 (필요시)