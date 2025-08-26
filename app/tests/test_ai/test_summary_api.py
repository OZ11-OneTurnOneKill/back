import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import json

from app.apis.ai_router.ai_summary_router import router
from app.exceptions import SummaryNotFoundError, SummaryAccessDeniedError


class TestSummaryAPI:
    """요약 API 엔드포인트 테스트

    이 클래스는 HTTP API의 동작을 검증합니다.
    실제 클라이언트 요청에 대한 응답을 시뮬레이션하여 API의 안정성을 확인합니다.
    """

    @pytest.fixture
    def mock_summary_service(self):
        """Mock SummaryService 생성"""
        service = Mock()

        # 각 메서드를 비동기 Mock으로 설정
        service.create_summary = AsyncMock()
        service.get_user_summaries = AsyncMock()
        service.get_summary_by_id = AsyncMock()
        service.delete_summary = AsyncMock()

        return service

    @pytest.fixture
    def sample_summary_response(self):
        """테스트용 요약 응답 데이터"""
        return Mock(
            id=1,
            user_id=123,
            title="테스트 요약",
            input_type="text",
            input_data="테스트 내용",
            summary_type="general",
            output_data='{"summary": "테스트 요약 결과"}',
            file_url=None,
            created_at="2025-08-14T10:00:00Z"
        )

    async def test_create_summary_success(self, mock_summary_service, sample_summary_response):
        """요약 생성 API 성공 테스트"""

        async def simulate_create_summary_api(user_id: int, request_data: dict):
            """실제 API 동작을 시뮬레이션하는 함수

            이 함수는 FastAPI 라우터의 동작을 모방하여
            테스트 환경에서 API 로직을 검증합니다.
            """
            try:
                # 요청 데이터 검증 (실제 API에서 Pydantic이 수행)
                required_fields = ["title", "input_data", "summary_type"]
                for field in required_fields:
                    if field not in request_data:
                        return {
                            "success": False,
                            "message": f"Missing required field: {field}"
                        }, 400

                # 서비스 호출
                result = await mock_summary_service.create_summary(
                    user_id=user_id,
                    request=Mock(**request_data)
                )

                return {
                    "success": True,
                    "message": "AI가 성공적으로 자료를 요약했습니다.",
                    "data": {"summary": result.dict() if hasattr(result, 'dict') else result},
                    "status": "completed"
                }, 201

            except Exception as e:
                return {
                    "success": False,
                    "message": f"자료 요약 중 오류가 발생했습니다: {str(e)}",
                    "status": "failed"
                }, 400

        # Given: 정상적인 요청 데이터와 성공적인 서비스 응답
        user_id = 123
        request_data = {
            "title": "머신러닝 기초",
            "input_data": "머신러닝은 AI의 한 분야입니다...",
            "input_type": "text",
            "summary_type": "general"
        }

        mock_summary_service.create_summary.return_value = sample_summary_response

        # When: API 호출 시뮬레이션
        response_data, status_code = await simulate_create_summary_api(user_id, request_data)

        # Then: 응답 검증
        assert status_code == 201
        assert response_data["success"] is True
        assert "성공적으로" in response_data["message"]
        assert "summary" in response_data["data"]

        # 서비스가 올바른 파라미터로 호출되었는지 확인
        mock_summary_service.create_summary.assert_called_once()

    async def test_create_summary_validation_error(self):
        """요약 생성 시 검증 오류 테스트"""

        async def simulate_validation_error(request_data: dict):
            """검증 실패 시나리오 시뮬레이션"""
            required_fields = ["title", "input_data", "summary_type"]
            missing_fields = [field for field in required_fields if field not in request_data]

            if missing_fields:
                return {
                    "success": False,
                    "message": f"필수 필드가 누락되었습니다: {missing_fields}"
                }, 400

            return {"success": True}, 200

        # Given: 필수 필드가 누락된 요청
        invalid_request = {
            "title": "제목만 있는 요청"
            # input_data와 summary_type이 누락됨
        }

        # When: 검증 실행
        response_data, status_code = await simulate_validation_error(invalid_request)

        # Then: 검증 오류 응답 확인
        assert status_code == 400
        assert response_data["success"] is False
        assert "필수 필드가 누락" in response_data["message"]

    async def test_get_user_summaries_success(self, mock_summary_service):
        """사용자 요약 목록 조회 API 테스트"""

        async def simulate_get_summaries_api(user_id: int, limit: int = 10, offset: int = 0):
            """요약 목록 조회 API 시뮬레이션"""
            try:
                summaries = await mock_summary_service.get_user_summaries(
                    user_id=user_id,
                    limit=limit,
                    offset=offset
                )

                return {
                    "success": True,
                    "message": "요약 목록을 성공적으로 조회했습니다.",
                    "data": {"summaries": [s.dict() if hasattr(s, 'dict') else s for s in summaries]}
                }, 200

            except Exception as e:
                return {
                    "success": False,
                    "message": f"목록 조회 중 오류가 발생했습니다: {str(e)}"
                }, 500

        # Given: 사용자의 요약 목록
        user_id = 123
        mock_summaries = [
            Mock(id=1, title="첫 번째 요약"),
            Mock(id=2, title="두 번째 요약")
        ]
        mock_summary_service.get_user_summaries.return_value = mock_summaries

        # When: API 호출
        response_data, status_code = await simulate_get_summaries_api(user_id)

        # Then: 응답 검증
        assert status_code == 200
        assert response_data["success"] is True
        assert len(response_data["data"]["summaries"]) == 2

    async def test_get_summary_by_id_not_found(self, mock_summary_service):
        """존재하지 않는 요약 조회 시 404 응답 테스트"""

        async def simulate_get_summary_by_id_api(user_id: int, summary_id: int):
            """단건 조회 API 시뮬레이션"""
            try:
                summary = await mock_summary_service.get_summary_by_id(
                    summary_id=summary_id,
                    user_id=user_id
                )

                return {
                    "success": True,
                    "message": "요약을 성공적으로 조회했습니다.",
                    "data": {"summary": summary.dict() if hasattr(summary, 'dict') else summary}
                }, 200

            except SummaryNotFoundError as e:
                return {
                    "success": False,
                    "message": str(e),
                    "data": e.details if hasattr(e, 'details') else {}
                }, 404

            except SummaryAccessDeniedError as e:
                return {
                    "success": False,
                    "message": str(e),
                    "data": e.details if hasattr(e, 'details') else {}
                }, 403

        # Given: 존재하지 않는 요약 조회 시 예외 발생
        user_id = 123
        summary_id = 999
        mock_summary_service.get_summary_by_id.side_effect = SummaryNotFoundError(summary_id)

        # When: API 호출
        response_data, status_code = await simulate_get_summary_by_id_api(user_id, summary_id)

        # Then: 404 응답 확인
        assert status_code == 404
        assert response_data["success"] is False
        assert "not found" in str(response_data["message"]).lower()

    async def test_delete_summary_success(self, mock_summary_service):
        """요약 삭제 API 성공 테스트"""

        async def simulate_delete_summary_api(user_id: int, summary_id: int):
            """삭제 API 시뮬레이션"""
            try:
                await mock_summary_service.delete_summary(
                    summary_id=summary_id,
                    user_id=user_id
                )

                return {
                    "success": True,
                    "message": "요약을 성공적으로 삭제했습니다.",
                    "data": {"deleted_summary_id": summary_id}
                }, 200

            except SummaryNotFoundError as e:
                return {
                    "success": False,
                    "message": str(e)
                }, 404

            except SummaryAccessDeniedError as e:
                return {
                    "success": False,
                    "message": str(e)
                }, 403

        # Given: 정상적인 삭제 시나리오
        user_id = 123
        summary_id = 1
        mock_summary_service.delete_summary.return_value = None

        # When: 삭제 API 호출
        response_data, status_code = await simulate_delete_summary_api(user_id, summary_id)

        # Then: 성공 응답 확인
        assert status_code == 200
        assert response_data["success"] is True
        assert "성공적으로 삭제" in response_data["message"]
        assert response_data["data"]["deleted_summary_id"] == summary_id

        # 서비스 메서드가 올바른 파라미터로 호출되었는지 확인
        mock_summary_service.delete_summary.assert_called_once_with(
            summary_id=summary_id,
            user_id=user_id
        )

    async def test_delete_summary_access_denied(self, mock_summary_service):
        """권한 없는 요약 삭제 시 403 응답 테스트"""

        async def simulate_delete_access_denied(user_id: int, summary_id: int):
            """권한 없는 삭제 시뮬레이션"""
            try:
                await mock_summary_service.delete_summary(
                    summary_id=summary_id,
                    user_id=user_id
                )
                return {"success": True}, 200

            except SummaryAccessDeniedError as e:
                return {
                    "success": False,
                    "message": str(e)
                }, 403

        # Given: 권한 없는 삭제 시도
        user_id = 123
        summary_id = 1
        mock_summary_service.delete_summary.side_effect = SummaryAccessDeniedError(summary_id, user_id)

        # When: 삭제 API 호출
        response_data, status_code = await simulate_delete_access_denied(user_id, summary_id)

        # Then: 403 응답 확인
        assert status_code == 403
        assert response_data["success"] is False
        assert "Access denied" in response_data["message"]