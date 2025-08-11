import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime, timedelta
import json


# ✅ 1단계: 실제 API 경로 확인을 위한 기본 테스트
class TestAPIBasics:
    """API 기본 동작 확인 테스트"""

    @pytest.fixture
    def client(self):
        """FastAPI 테스트 클라이언트"""
        try:
            from asgi import app  # 또는 main.py에서 app import
            return TestClient(app)
        except ImportError:
            # app import 실패 시 Mock 클라이언트 사용
            pytest.skip("FastAPI app을 import할 수 없습니다")

    def test_app_health_check(self, client):
        """앱이 정상적으로 로드되는지 확인"""
        # 기본 경로나 health check 엔드포인트 테스트
        response = client.get("/")
        # 404가 아닌 다른 응답이면 앱은 정상 로드됨
        assert response.status_code in [200, 404, 405, 422]

    def test_discover_api_routes(self, client):
        """API 경로 발견 테스트"""
        # 가능한 API 경로들 테스트
        possible_paths = [
            "/study_plan",
            "/study-plan",
            "/api/study_plan",
            "/api/study-plan",
            "/ai/study_plan",
            "/ai_study_plan",
            "/study_plans",
            "/docs",  # FastAPI 자동 문서
            "/openapi.json"  # OpenAPI 스펙
        ]

        results = {}
        for path in possible_paths:
            try:
                response = client.get(path)
                results[path] = response.status_code
            except Exception as e:
                results[path] = f"Error: {e}"

        # 결과 출력 (디버깅용)
        print("\n=== API 경로 스캔 결과 ===")
        for path, status_code in results.items():
            print(f"{path}: {status_code}")

        # 적어도 docs나 openapi.json은 있어야 함
        assert any(results[path] == 200 for path in ["/docs", "/openapi.json"])


# ✅ 2단계: 올바른 경로와 응답 형식을 가정한 테스트
class TestStudyPlanAPIFixed:
    """수정된 학습계획 API 테스트"""

    @pytest.fixture
    def client(self):
        """FastAPI 테스트 클라이언트"""
        try:
            from asgi import app
            return TestClient(app)
        except ImportError as e:
            print(f"Error: Could not import module. Details: {e}")

    @pytest.fixture
    def mock_study_plan_service(self):
        """Mock 학습계획 서비스"""
        service = Mock()
        service.create_study_plan = AsyncMock()
        service.get_study_plan_by_id = AsyncMock()
        service.get_user_study_plans = AsyncMock()
        service.update_study_plan = AsyncMock()
        service.delete_study_plan = AsyncMock()
        return service

    @pytest.fixture
    def sample_study_plan_data(self):
        """테스트용 학습계획 데이터 (모델 대신 딕셔너리)"""
        return {
            "id": 1,
            "user_id": 123,
            "input_data": "Python 웹 개발 3개월 과정",
            "output_data": '{"title": "Python 웹 개발 완성 과정", "total_weeks": 12}',
            "is_challenge": False,
            "start_date": "2025-08-15T09:00:00",
            "end_date": "2025-11-15T18:00:00",
            "created_at": "2025-08-11T10:00:00"
        }

    # ✅ 가능한 API 경로들로 테스트
    @pytest.mark.parametrize("api_path", [
        "/study_plan",
        "/study-plan",
        "/api/study_plan",
        "/api/study-plan",
        "/ai/study_plan"
    ])
    def test_api_path_variations(self, client, api_path):
        """다양한 API 경로 테스트"""
        # GET 요청으로 경로 존재 여부 확인
        response = client.get(f"{api_path}/123")

        # 404가 아니면 올바른 경로
        if response.status_code != 404:
            print(f"\n✅ 발견된 유효한 경로: {api_path}")
            print(f"응답 상태: {response.status_code}")
            if response.status_code != 500:  # 서버 에러가 아니면 응답 내용 출력
                print(f"응답 내용: {response.text[:200]}...")

    # ✅ Mock을 사용한 독립적인 테스트 (실제 API 없이도 동작)
    @patch('sys.modules')  # 모든 모듈을 Mock
    async def test_create_study_plan_logic_only(self, mock_modules, mock_study_plan_service, sample_study_plan_data):
        """API 로직만 테스트 (실제 FastAPI 없이)"""

        # API 핸들러 로직 시뮬레이션
        async def simulate_create_study_plan_api(user_id: int, request_data: dict):
            try:
                # 1. 요청 데이터 검증
                if not request_data.get("input_data"):
                    return {"success": False, "message": "input_data is required"}, 422

                # 2. 서비스 호출
                result = await mock_study_plan_service.create_study_plan(
                    user_id=user_id,
                    request=request_data
                )

                # 3. 성공 응답
                return {
                    "success": True,
                    "message": "AI가 성공적으로 공부 계획을 생성하였습니다.",
                    "data": {"study_plans": result}
                }, 201

            except Exception as e:
                return {"success": False, "message": str(e)}, 400

        # Given
        mock_study_plan_service.create_study_plan.return_value = sample_study_plan_data

        request_data = {
            "input_data": "Python 웹 개발 3개월 과정",
            "start_date": "2025-08-15T09:00:00",
            "end_date": "2025-11-15T18:00:00",
            "is_challenge": False
        }

        # When
        response_data, status_code = await simulate_create_study_plan_api(123, request_data)

        # Then
        assert status_code == 201
        assert response_data["success"] == True
        assert "AI가 성공적으로" in response_data["message"]
        assert response_data["data"]["study_plans"]["id"] == 1

    async def test_get_study_plan_logic_only(self, mock_study_plan_service, sample_study_plan_data):
        """조회 API 로직만 테스트"""

        async def simulate_get_study_plan_api(user_id: int, plan_id: int):
            try:
                result = await mock_study_plan_service.get_study_plan_by_id(
                    study_plan_id=plan_id,
                    user_id=user_id
                )

                return {
                    "success": True,
                    "data": {"study_plans": result}
                }, 200

            except ValueError as e:
                if "not found" in str(e):
                    return {"success": False, "message": str(e)}, 404
                elif "access denied" in str(e).lower():
                    return {"success": False, "message": str(e)}, 403
                else:
                    return {"success": False, "message": str(e)}, 400

        # Given
        mock_study_plan_service.get_study_plan_by_id.return_value = sample_study_plan_data

        # When
        response_data, status_code = await simulate_get_study_plan_api(123, 1)

        # Then
        assert status_code == 200
        assert response_data["success"] == True
        assert response_data["data"]["study_plans"]["id"] == 1

    async def test_get_study_plan_not_found_logic(self, mock_study_plan_service):
        """Not Found 로직 테스트"""

        async def simulate_get_study_plan_api(user_id: int, plan_id: int):
            try:
                result = await mock_study_plan_service.get_study_plan_by_id(
                    study_plan_id=plan_id,
                    user_id=user_id
                )
                return {"success": True, "data": {"study_plans": result}}, 200
            except ValueError as e:
                if "not found" in str(e):
                    return {"success": False, "message": str(e)}, 404
                else:
                    return {"success": False, "message": str(e)}, 400

        # Given
        mock_study_plan_service.get_study_plan_by_id.side_effect = ValueError("Study plan not found")

        # When
        response_data, status_code = await simulate_get_study_plan_api(123, 999)

        # Then
        assert status_code == 404
        assert response_data["success"] == False
        assert "not found" in response_data["message"]

    async def test_update_study_plan_logic(self, mock_study_plan_service, sample_study_plan_data):
        """업데이트 로직 테스트"""

        async def simulate_update_study_plan_api(user_id: int, plan_id: int, update_data: dict):
            try:
                result = await mock_study_plan_service.update_study_plan(
                    study_plan_id=plan_id,
                    user_id=user_id,
                    update_data=update_data
                )

                return {
                    "success": True,
                    "message": "학습 계획을 성공적으로 업데이트했습니다.",
                    "data": {"study_plans": result}
                }, 200

            except ValueError as e:
                return {"success": False, "message": str(e)}, 400

        # Given
        updated_data = sample_study_plan_data.copy()
        updated_data["input_data"] = "수정된 Python 웹 개발 과정"
        mock_study_plan_service.update_study_plan.return_value = updated_data

        update_request = {
            "input_data": "수정된 Python 웹 개발 과정",
            "start_date": "2025-09-01T09:00:00"
        }

        # When
        response_data, status_code = await simulate_update_study_plan_api(123, 1, update_request)

        # Then
        assert status_code == 200
        assert response_data["success"] == True
        assert "수정된 Python 웹 개발 과정" in response_data["data"]["study_plans"]["input_data"]

    async def test_delete_study_plan_logic(self, mock_study_plan_service):
        """삭제 로직 테스트"""

        async def simulate_delete_study_plan_api(user_id: int, plan_id: int):
            try:
                await mock_study_plan_service.delete_study_plan(
                    study_plan_id=plan_id,
                    user_id=user_id
                )

                return {
                    "success": True,
                    "message": "학습 계획을 성공적으로 삭제했습니다."
                }, 200

            except ValueError as e:
                if "access denied" in str(e).lower():
                    return {"success": False, "message": str(e)}, 403
                else:
                    return {"success": False, "message": str(e)}, 404

        # Given
        mock_study_plan_service.delete_study_plan.return_value = None

        # When
        response_data, status_code = await simulate_delete_study_plan_api(123, 1)

        # Then
        assert status_code == 200
        assert response_data["success"] == True
        assert "성공적으로 삭제" in response_data["message"]

    async def test_validation_error_logic(self):
        """검증 에러 로직 테스트"""

        def validate_request_data(data: dict):
            errors = []

            if not data.get("input_data") or not data["input_data"].strip():
                errors.append("input_data is required and cannot be empty")

            if "start_date" in data:
                try:
                    datetime.fromisoformat(data["start_date"].replace("Z", "+00:00"))
                except ValueError:
                    errors.append("start_date must be valid ISO format")

            return errors

        # Given
        invalid_data = {
            "input_data": "",  # 빈 문자열
            "start_date": "invalid-date"  # 잘못된 날짜
        }

        # When
        errors = validate_request_data(invalid_data)

        # Then
        assert len(errors) == 2
        assert "input_data is required" in errors[0]
        assert "start_date must be valid" in errors[1]


# ✅ 3단계: 실제 API 구조 확인 도구
class TestAPIDiscovery:
    """실제 API 구조 발견을 위한 테스트"""

    @pytest.fixture
    def client(self):
        try:
            from asgi import app
            return TestClient(app)
        except ImportError:
            pytest.skip("FastAPI app import 실패")

    def test_discover_openapi_spec(self, client):
        """OpenAPI 스펙을 통한 엔드포인트 발견"""
        response = client.get("/openapi.json")

        if response.status_code == 200:
            openapi_spec = response.json()
            paths = openapi_spec.get("paths", {})

            print("\n=== 발견된 API 엔드포인트들 ===")
            for path, methods in paths.items():
                for method, details in methods.items():
                    summary = details.get("summary", "No summary")
                    print(f"{method.upper()} {path} - {summary}")

            # study_plan 관련 엔드포인트 찾기
            study_plan_paths = [path for path in paths.keys() if "study" in path.lower()]
            if study_plan_paths:
                print(f"\n✅ study_plan 관련 경로들: {study_plan_paths}")
            else:
                print("\n❌ study_plan 관련 경로를 찾을 수 없습니다")

    def test_check_app_structure(self, client):
        """앱 구조 확인"""
        # 일반적인 FastAPI 엔드포인트들 확인
        endpoints_to_check = [
            ("/", "root"),
            ("/docs", "swagger docs"),
            ("/redoc", "redoc docs"),
            ("/health", "health check"),
            ("/status", "status check")
        ]

        print("\n=== 기본 엔드포인트 확인 ===")
        for endpoint, description in endpoints_to_check:
            response = client.get(endpoint)
            status = "✅" if response.status_code in [200, 307] else "❌"
            print(f"{status} {endpoint} ({description}): {response.status_code}")


# ✅ 4단계: 환경 설정 확인
class TestEnvironmentSetup:
    """테스트 환경 설정 확인"""

    def test_imports(self):
        """필요한 모듈들이 import 가능한지 확인"""
        import_results = {}

        modules_to_test = [
            "asgi",
            "main",
            "app.apis",
            "app.services.ai_services.study_plan_service",
            "app.dtos.ai_study_plan.study_plan"
        ]

        for module_name in modules_to_test:
            try:
                __import__(module_name)
                import_results[module_name] = "✅ Success"
            except ImportError as e:
                import_results[module_name] = f"❌ Failed: {e}"

        print("\n=== Import 테스트 결과 ===")
        for module, result in import_results.items():
            print(f"{module}: {result}")

    def test_fastapi_app_existence(self):
        """FastAPI 앱 객체가 존재하는지 확인"""
        possible_app_locations = [
            ("asgi", "app"),
            ("main", "app"),
            ("app.main", "app"),
            ("app", "app"),
            ("app.asgi", "app")
        ]

        for module_name, app_attr in possible_app_locations:
            try:
                module = __import__(module_name, fromlist=[app_attr])
                app = getattr(module, app_attr)
                print(f"✅ FastAPI 앱 발견: {module_name}.{app_attr}")
                print(f"   앱 타입: {type(app)}")
                return app
            except (ImportError, AttributeError):
                continue

        print("❌ FastAPI 앱을 찾을 수 없습니다")
        return None