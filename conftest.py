import pytest
import httpx
import sys
import json
import asyncio
from app import app   # FastAPI 앱 (app/__init__.py 에 있는 app)
from tortoise.contrib.test import initializer, finalizer
from app.apis.community.like_router import post_views
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List


@pytest.fixture(scope="session", autouse=True)
def initialize_tests():
    initializer(["app.models.community", "app.models.user", "app.models.ai"])
    yield
    finalizer()


@pytest.fixture
async def async_client():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture(autouse=True)
def clear_post_views():
    post_views.clear()
    yield
    post_views.clear()

    # =============================================================================
    # pytest 설정 및 이벤트 루프 관리
    # =============================================================================

    def pytest_configure(config):
        """pytest 설정 초기화

        테스트 실행 전에 필요한 전역 설정을 수행합니다.
        이는 마치 무대 공연 전에 조명과 음향을 점검하는 것과 같습니다.
        """
        # 경고 메시지 억제
        import warnings
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

    @pytest.fixture(scope="session")
    def event_loop():
        """세션 범위의 이벤트 루프

        모든 비동기 테스트에서 사용할 이벤트 루프를 제공합니다.
        이를 통해 테스트 간 일관성을 보장합니다.
        """
        loop = asyncio.new_event_loop()
        yield loop
        loop.close()

    # =============================================================================
    # Tortoise ORM 완전 차단 시스템
    # =============================================================================

    @pytest.fixture(scope="session", autouse=True)
    def block_all_external_dependencies():
        """모든 외부 의존성을 완전히 차단

        이 fixture는 테스트 시작 전에 자동으로 실행되어
        모든 외부 시스템과의 연결을 차단합니다.

        차단 대상:
        - Tortoise ORM의 모든 모듈
        - 실제 데이터베이스 연결
        - 외부 API 호출
        - 파일 시스템 접근
        """

        # 1. Tortoise ORM 핵심 모듈들을 Mock으로 완전 대체
        tortoise_modules_to_mock = [
            'tortoise',
            'tortoise.models',
            'tortoise.fields',
            'tortoise.exceptions',
            'tortoise.transactions',
            'tortoise.connection',
            'tortoise.backends',
            'tortoise.query_utils'
        ]

        original_modules = {}
        for module_name in tortoise_modules_to_mock:
            if module_name in sys.modules:
                original_modules[module_name] = sys.modules[module_name]

            # 완전한 Mock 모듈 생성
            mock_module = create_comprehensive_tortoise_mock(module_name)
            sys.modules[module_name] = mock_module

        # 2. 모델 모듈들도 Mock으로 대체
        model_modules_to_mock = [
            'app.models',
            'app.models.ai',
            'app.models.study_plan',
            'app.models.summary'
        ]

        for model_module in model_modules_to_mock:
            mock_models = create_mock_model_module()
            sys.modules[model_module] = mock_models

        yield

        # 테스트 완료 후 원본 모듈 복원 (필요시)
        for module_name, original_module in original_modules.items():
            sys.modules[module_name] = original_module

    def create_comprehensive_tortoise_mock(module_name: str) -> MagicMock:
        """포괄적인 Tortoise ORM Mock 생성

        실제 Tortoise ORM의 모든 주요 기능을 Mock으로 대체합니다.
        이는 마치 실제 엔진 대신 시뮬레이터를 사용하는 것과 같습니다.
        """
        mock_module = MagicMock()
        mock_module.__name__ = module_name

        if module_name == 'tortoise':
            # 메인 Tortoise 모듈의 핵심 기능들
            mock_module.init = AsyncMock()
            mock_module.close_connections = AsyncMock()
            mock_module.generate_schemas = AsyncMock()
            mock_module.Tortoise = MagicMock()

            # 트랜잭션 관련 Mock
            mock_transaction_context = MagicMock()
            mock_transaction_context.__aenter__ = AsyncMock()
            mock_transaction_context.__aexit__ = AsyncMock()
            mock_module.transactions = MagicMock()
            mock_module.transactions.in_transaction = Mock(return_value=mock_transaction_context)

        elif module_name == 'tortoise.models':
            # Model 기본 클래스 Mock
            mock_module.Model = MagicMock()

        elif module_name == 'tortoise.fields':
            # 필드 타입들 Mock
            field_types = ['IntField', 'CharField', 'TextField', 'DatetimeField',
                           'BooleanField', 'ForeignKeyField', 'JSONField']
            for field_type in field_types:
                setattr(mock_module, field_type, MagicMock())

        elif module_name == 'tortoise.exceptions':
            # 예외 클래스들 Mock
            exception_types = ['DoesNotExist', 'MultipleObjectsReturned',
                               'ValidationError', 'ConfigurationError', 'ParamsError']
            for exc_type in exception_types:
                # 실제 예외처럼 동작하는 Mock 클래스 생성
                mock_exception = type(exc_type, (Exception,), {})
                setattr(mock_module, exc_type, mock_exception)

        return mock_module

    def create_mock_model_module() -> MagicMock:
        """모델 모듈 Mock 생성

        StudyPlan, DocumentSummary 등의 모델 클래스를 Mock으로 생성합니다.
        """
        mock_module = MagicMock()

        # StudyPlan 모델 Mock
        mock_study_plan = create_model_class_mock('StudyPlan')
        mock_module.StudyPlan = mock_study_plan

        # DocumentSummary 모델 Mock
        mock_document_summary = create_model_class_mock('DocumentSummary')
        mock_module.DocumentSummary = mock_document_summary

        return mock_module

    def create_model_class_mock(model_name: str) -> MagicMock:
        """개별 모델 클래스 Mock 생성

        실제 Tortoise 모델의 모든 메서드를 정확히 모방합니다.
        """
        mock_class = MagicMock()
        mock_class.__name__ = model_name

        # CRUD 메서드들
        mock_class.create = AsyncMock()
        mock_class.get = AsyncMock()
        mock_class.get_or_none = AsyncMock()
        mock_class.filter = Mock()
        mock_class.all = Mock()
        mock_class.delete = AsyncMock()
        mock_class.update = AsyncMock()
        mock_class.save = AsyncMock()
        mock_class.bulk_create = AsyncMock()

        # QuerySet을 반환하는 메서드들
        def create_queryset_mock():
            queryset = Mock()
            queryset.order_by = Mock(return_value=queryset)
            queryset.limit = Mock(return_value=queryset)
            queryset.offset = Mock(return_value=queryset)
            queryset.filter = Mock(return_value=queryset)
            queryset.exclude = Mock(return_value=queryset)
            queryset.count = AsyncMock(return_value=0)
            queryset.exists = AsyncMock(return_value=False)
            queryset.first = AsyncMock(return_value=None)
            queryset.values = Mock(return_value=queryset)
            queryset.values_list = Mock(return_value=queryset)
            queryset.distinct = Mock(return_value=queryset)
            return queryset

        mock_class.filter.return_value = create_queryset_mock()
        mock_class.all.return_value = create_queryset_mock()

        return mock_class

    # =============================================================================
    # Gemini API Mock 시스템
    # =============================================================================

    @pytest.fixture
    def mock_gemini_ecosystem():
        """Gemini API 생태계 완전 Mock

        이 fixture는 모든 Gemini 관련 기능을 Mock으로 대체합니다.
        fixture 이름을 간단하게 하여 사용하기 쉽도록 했습니다.
        """
        with patch('app.services.ai_services.gemini_service.genai') as mock_genai:
            # 기본 Mock 설정
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = Mock()

            # 응답 생성 헬퍼 함수
            def create_mock_response(content: str):
                mock_response = Mock()
                mock_response.text = content
                return mock_response

            # 기본 성공 응답들
            default_study_plan = {
                "title": "기본 학습계획",
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

            default_summary = {
                "title": "기본 요약",
                "summary_type": "general",
                "summary": "기본 요약 내용입니다.",
                "key_points": ["포인트 1", "포인트 2"],
                "word_count": 100,
                "summary_ratio": "50%"
            }

            # 기본 응답 설정
            mock_model.generate_content_async = AsyncMock(
                return_value=create_mock_response(json.dumps(default_study_plan))
            )

            yield {
                'genai': mock_genai,
                'model': mock_model,
                'create_response': create_mock_response,
                'default_study_plan': default_study_plan,
                'default_summary': default_summary
            }

    # =============================================================================
    # 테스트 데이터 Fixtures
    # =============================================================================

    @pytest.fixture
    def study_plan_test_data():
        """학습계획 테스트용 데이터"""
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
                        "title": "Python 기초 문법",
                        "topics": ["변수", "제어문", "함수"],
                        "goals": ["기본 문법 이해"],
                        "estimated_hours": 15
                    }
                ],
                "milestones": [
                    {"week": 4, "milestone": "Python 기초 완료"}
                ]
            }
        }

    @pytest.fixture
    def summary_test_data():
        """요약 테스트용 데이터"""
        return {
            'user_id': 456,
            'summary_id': 2,
            'request_data': {
                'title': "AI와 머신러닝 핵심 개념",
                'input_data': "인공지능(AI)은 컴퓨터가 인간과 같은 지능을 구현하는 기술입니다.",
                'input_type': 'text',
                'summary_type': 'general',
                'file_url': None
            },
            'ai_response': {
                "title": "AI와 머신러닝 핵심 개념",
                "summary_type": "general",
                "summary": "AI는 컴퓨터가 인간과 같은 지능을 구현하는 기술입니다.",
                "key_points": [
                    "AI는 인간과 같은 지능 구현",
                    "머신러닝은 데이터 기반 학습"
                ],
                "word_count": 50,
                "summary_ratio": "25%"
            }
        }

    @pytest.fixture
    def error_scenarios():
        """다양한 에러 시나리오 데이터"""
        return {
            'not_found': {
                'study_plan_id': 999,
                'summary_id': 999,
                'user_id': 123
            },
            'access_denied': {
                'owner_user_id': 123,
                'other_user_id': 456
            },
            'api_errors': {
                'rate_limit': "API Rate Limit Exceeded",
                'network_error': "Network Connection Failed",
                'invalid_response': "Invalid JSON response"
            }
        }

    # =============================================================================
    # 데이터베이스 Mock Fixtures
    # =============================================================================

    @pytest.fixture
    def mock_tortoise_ecosystem():
        """Tortoise ORM 생태계 Mock

        이 fixture는 자동 적용되는 Mock 시스템 위에서
        개별 테스트에서 필요한 Mock 객체들을 쉽게 접근할 수 있게 해줍니다.
        """
        # sys.modules에서 Mock된 모델들 가져오기
        mock_ai_models = sys.modules.get('app.models.ai', MagicMock())

        return {
            'StudyPlan': mock_ai_models.StudyPlan,
            'DocumentSummary': mock_ai_models.DocumentSummary
        }

    # =============================================================================
    # 로깅 및 환경 설정
    # =============================================================================

    @pytest.fixture(autouse=True)
    def configure_test_logging():
        """테스트 로깅 설정

        테스트 실행 중 불필요한 로그 메시지를 최소화합니다.
        """
        import logging

        # 로깅 레벨 조정
        logging.getLogger().setLevel(logging.WARNING)
        logging.getLogger('app').setLevel(logging.ERROR)
        logging.getLogger('tortoise').setLevel(logging.CRITICAL)

        # HTTP 클라이언트 로그 억제
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)

        yield

        # 테스트 완료 후 로깅 레벨 복원 (필요시)

    # =============================================================================
    # 유틸리티 함수들
    # =============================================================================

    def create_mock_response_instance(model_name: str, test_data: Dict[str, Any]) -> Mock:
        """응답 인스턴스 Mock 생성 유틸리티

        테스트에서 자주 사용되는 응답 객체 Mock을 생성합니다.
        """
        mock_instance = Mock()

        if model_name == 'StudyPlan':
            mock_instance.id = test_data.get('study_plan_id', 1)
            mock_instance.user_id = test_data.get('user_id', 123)
            mock_instance.input_data = test_data.get('request_data', {}).get('input_data', '')
            mock_instance.output_data = json.dumps(test_data.get('ai_response', {}))
            mock_instance.is_challenge = test_data.get('request_data', {}).get('is_challenge', False)
            mock_instance.start_date = test_data.get('request_data', {}).get('start_date', datetime.now())
            mock_instance.end_date = test_data.get('request_data', {}).get('end_date', datetime.now())
            mock_instance.created_at = datetime.now()

        elif model_name == 'DocumentSummary':
            mock_instance.id = test_data.get('summary_id', 1)
            mock_instance.user_id = test_data.get('user_id', 123)
            mock_instance.title = test_data.get('request_data', {}).get('title', '')
            mock_instance.input_type = test_data.get('request_data', {}).get('input_type', 'text')
            mock_instance.input_data = test_data.get('request_data', {}).get('input_data', '')
            mock_instance.summary_type = test_data.get('request_data', {}).get('summary_type', 'general')
            mock_instance.output_data = json.dumps(test_data.get('ai_response', {}))
            mock_instance.file_url = test_data.get('request_data', {}).get('file_url')
            mock_instance.created_at = datetime.now()

        # 공통 메서드들
        mock_instance.save = AsyncMock()
        mock_instance.delete = AsyncMock()
        mock_instance.update_from_dict = Mock(return_value=mock_instance)

        return mock_instance