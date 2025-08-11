# conftest.py (테스트 디렉토리에 생성)
import pytest
import sys
from unittest.mock import Mock, AsyncMock, MagicMock


# ✅ 가장 간단하고 효과적인 방법
@pytest.fixture(scope="session", autouse=True)
def mock_tortoise_orm():
    """Tortoise ORM을 완전히 Mock으로 교체"""

    # 실제 모델 import 전에 Mock 모듈 생성
    mock_study_plan_module = MagicMock()

    # StudyPlan 클래스 Mock
    mock_study_plan_class = MagicMock()
    mock_study_plan_class.__name__ = 'StudyPlan'

    # 자주 사용되는 메서드들을 미리 설정
    mock_study_plan_class.create = Mock()
    mock_study_plan_class.get_or_none = Mock()
    mock_study_plan_class.get = Mock()
    mock_study_plan_class.filter = Mock()
    mock_study_plan_class.all = Mock()

    # 모듈에 클래스 연결
    mock_study_plan_module.StudyPlan = mock_study_plan_class

    # sys.modules에 등록 (여러 경로로 시도)
    sys.modules['app.models.study_plan'] = mock_study_plan_module
    sys.modules['app.models.ai'] = mock_study_plan_module

    # Tortoise ORM 자체도 Mock
    mock_tortoise = MagicMock()
    mock_tortoise.init = AsyncMock()
    mock_tortoise.close_connections = AsyncMock()
    mock_tortoise.generate_schemas = AsyncMock()

    sys.modules['tortoise'] = mock_tortoise
    sys.modules['tortoise.models'] = MagicMock()
    sys.modules['tortoise.fields'] = MagicMock()

    yield mock_study_plan_class


# ✅ 각 테스트에서 사용할 공통 fixture들
@pytest.fixture
def mock_gemini_service():
    """Mock Gemini 서비스"""
    service = Mock()
    service.generate_study_plan = AsyncMock()
    return service


@pytest.fixture
def sample_request():
    """테스트용 요청 데이터"""
    # 실제 import 없이 딕셔너리로 구성
    return {
        'input_data': "Python 웹 개발 3개월 과정",
        'start_date': "2025-08-15T09:00:00",
        'end_date': "2025-11-15T18:00:00",
        'is_challenge': False
    }


@pytest.fixture
def sample_ai_response():
    """테스트용 AI 응답"""
    return {
        "title": "Python 웹 개발 완성 과정",
        "total_weeks": 12,
        "weekly_plans": [],
        "milestones": []
    }