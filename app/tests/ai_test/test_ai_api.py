import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from tortoise import Tortoise
from app.models.user import UserModel, SocialAccountModel, ProviderType
from app.models.ai_study_plan import AIStudyPlan
from app import app

client = TestClient(app)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    """Setup test database"""
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["app.models.user", "app.models.ai_study_plan", "app.models.base_model"]}
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest_asyncio.fixture
async def test_user():
    """Create test user"""
    social_account = await SocialAccountModel.create(
        provider=ProviderType.GOOGLE,
        provider_id="test_google_123",
        email="test@example.com"
    )
    user = await UserModel.create(
        social_account=social_account,
        nickname="testuser",
        profile_image_url="https://example.com/profile.jpg"
    )
    return user


@pytest.fixture
def test_study_plan_data():
    """Create test study plan data"""
    return {
        "user_id": 1,
        "is_challenge": False,
        "input_data": "I want to learn Python for web development in 30 days",
        "start_date": datetime.now().isoformat(),
        "end_date": (datetime.now() + timedelta(days=30)).isoformat()
    }


@pytest_asyncio.fixture(autouse=True)
async def cleanup_data():
    """Clean up test data after each test"""
    yield
    # Clean up in reverse dependency order
    await AIStudyPlan.all().delete()
    await UserModel.all().delete()
    await SocialAccountModel.all().delete()


@pytest.mark.asyncio
class TestAIStudyPlanAPI:
    """AI 스터디 플랜 API 엔드포인트 테스트"""
    
    async def test_create_study_plan(self, test_user, test_study_plan_data):
        """스터디 플랜 생성 API 테스트"""
        test_study_plan_data["user_id"] = test_user.id
        
        response = client.post("/api/v1/ai/study-plans", json=test_study_plan_data)
        
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text}")
        
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == test_user.id
        assert data["input_data"] == test_study_plan_data["input_data"]
        assert data["is_challenge"] == False
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "status" in data
        assert "progress_percentage" in data
        assert "days_remaining" in data
    
    async def test_create_challenge_study_plan(self, test_user):
        """챌린지 스터디 플랜 생성 API 테스트"""
        challenge_data = {
            "user_id": test_user.id,
            "is_challenge": True,
            "input_data": "30-day coding challenge",
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=30)).isoformat()
        }
        
        response = client.post("/api/v1/ai/study-plans", json=challenge_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["is_challenge"] == True
        assert data["user_id"] == test_user.id
    
    async def test_create_study_plan_invalid_data(self, test_user):
        """잘못된 데이터로 스터디 플랜 생성 시 실패 테스트"""
        invalid_data = {
            "user_id": test_user.id,
            "input_data": "Test input"
            # 필수 필드들 누락
        }
        
        response = client.post("/api/v1/ai/study-plans", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    async def test_create_study_plan_invalid_date_range(self, test_user):
        """잘못된 날짜 범위로 스터디 플랜 생성 시 실패 테스트"""
        invalid_date_data = {
            "user_id": test_user.id,
            "is_challenge": False,
            "input_data": "Test input",
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() - timedelta(days=1)).isoformat()  # 시작일보다 이른 종료일
        }
        
        response = client.post("/api/v1/ai/study-plans", json=invalid_date_data)
        assert response.status_code == 400
    
    async def test_create_study_plan_nonexistent_user(self):
        """존재하지 않는 사용자로 스터디 플랜 생성 시 실패 테스트"""
        invalid_user_data = {
            "user_id": 99999,  # 존재하지 않는 사용자
            "is_challenge": False,
            "input_data": "Test input",
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=30)).isoformat()
        }
        
        response = client.post("/api/v1/ai/study-plans", json=invalid_user_data)
        assert response.status_code == 404
    
    async def test_get_study_plan_by_id(self, test_user, test_study_plan_data):
        """ID로 스터디 플랜 조회 API 테스트"""
        test_study_plan_data["user_id"] = test_user.id
        
        create_response = client.post("/api/v1/ai/study-plans", json=test_study_plan_data)
        created_plan = create_response.json()
        plan_id = created_plan["id"]
        
        response = client.get(f"/api/v1/ai/study-plans/{plan_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == plan_id
        assert data["user_id"] == test_user.id
        assert data["input_data"] == test_study_plan_data["input_data"]
    
    async def test_get_nonexistent_study_plan(self):
        """존재하지 않는 스터디 플랜 조회 시 404 에러 테스트"""
        response = client.get("/api/v1/ai/study-plans/9999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    async def test_get_study_plans_with_filters(self, test_user):
        """필터를 사용한 스터디 플랜 목록 조회 API 테스트"""
        # 챌린지 플랜 생성
        await AIStudyPlan.create(
            user_id=test_user.id,
            is_challenge=True,
            input_data="Challenge plan 1",
            output_data="Challenge output 1",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30)
        )
        
        # 일반 플랜 생성
        await AIStudyPlan.create(
            user_id=test_user.id,
            is_challenge=False,
            input_data="Regular plan 1",
            output_data="Regular output 1",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=20)
        )
        
        response = client.get(f"/api/v1/ai/study-plans?user_id={test_user.id}&is_challenge=true")
        
        assert response.status_code == 200
        data = response.json()
        plans = data if isinstance(data, list) else data.get("items", data)
        assert len(plans) >= 1
        for plan in plans:
            assert plan["user_id"] == test_user.id
            assert plan["is_challenge"] == True
    
    async def test_get_study_plans_pagination(self, test_user):
        """페이징을 사용한 스터디 플랜 목록 조회 API 테스트"""
        # 여러 개의 스터디 플랜 생성
        for i in range(5):
            await AIStudyPlan.create(
                user_id=test_user.id,
                is_challenge=False,
                input_data=f"Plan {i}",
                output_data=f"Output {i}",
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30)
            )
        
        # 첫 번째 페이지 조회
        response = client.get(f"/api/v1/ai/study-plans?user_id={test_user.id}&limit=3&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        plans = data if isinstance(data, list) else data.get("items", data)
        assert len(plans) <= 3
        
        # 두 번째 페이지 조회
        response = client.get(f"/api/v1/ai/study-plans?user_id={test_user.id}&limit=3&offset=3")
        
        assert response.status_code == 200
        data = response.json()
        plans = data if isinstance(data, list) else data.get("items", data)
        assert isinstance(plans, list)
    
    async def test_update_study_plan(self, test_user, test_study_plan_data):
        """스터디 플랜 업데이트 API 테스트"""
        test_study_plan_data["user_id"] = test_user.id
        
        create_response = client.post("/api/v1/ai/study-plans", json=test_study_plan_data)
        created_plan = create_response.json()
        plan_id = created_plan["id"]
        
        update_data = {
            "input_data": "Updated learning goal",
            "is_challenge": True
        }
        
        response = client.put(f"/api/v1/ai/study-plans/{plan_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["input_data"] == update_data["input_data"]
        assert data["is_challenge"] == True
    
    async def test_update_nonexistent_study_plan(self):
        """존재하지 않는 스터디 플랜 업데이트 시 404 에러 테스트"""
        update_data = {"input_data": "Updated content"}
        response = client.put("/api/v1/ai/study-plans/9999", json=update_data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    async def test_update_study_plan_invalid_date_range(self, test_user, test_study_plan_data):
        """잘못된 날짜 범위로 스터디 플랜 업데이트 시 실패 테스트"""
        test_study_plan_data["user_id"] = test_user.id
        
        create_response = client.post("/api/v1/ai/study-plans", json=test_study_plan_data)
        created_plan = create_response.json()
        plan_id = created_plan["id"]
        
        invalid_update_data = {
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() - timedelta(days=5)).isoformat()
        }
        
        response = client.put(f"/api/v1/ai/study-plans/{plan_id}", json=invalid_update_data)
        assert response.status_code == 400
    
    async def test_delete_study_plan(self, test_user, test_study_plan_data):
        """스터디 플랜 삭제 API 테스트"""
        test_study_plan_data["user_id"] = test_user.id
        
        create_response = client.post("/api/v1/ai/study-plans", json=test_study_plan_data)
        created_plan = create_response.json()
        plan_id = created_plan["id"]
        
        response = client.delete(f"/api/v1/ai/study-plans/{plan_id}")
        
        assert response.status_code == 204  # No Content
        
        # 삭제된 플랜 조회 시 404 에러 확인
        get_response = client.get(f"/api/v1/ai/study-plans/{plan_id}")
        assert get_response.status_code == 404
    
    async def test_delete_nonexistent_study_plan(self):
        """존재하지 않는 스터디 플랜 삭제 시 404 에러 테스트"""
        response = client.delete("/api/v1/ai/study-plans/9999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    async def test_get_user_study_plans(self, test_user):
        """특정 사용자의 스터디 플랜 목록 조회 API 테스트"""
        # 테스트 데이터 생성
        await AIStudyPlan.create(
            user_id=test_user.id,
            is_challenge=True,
            input_data="Challenge plan",
            output_data="Challenge output",
            start_date=datetime.now() - timedelta(days=10),
            end_date=datetime.now() + timedelta(days=20)
        )
        
        await AIStudyPlan.create(
            user_id=test_user.id,
            is_challenge=False,
            input_data="Regular plan",
            output_data="Regular output",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now() - timedelta(days=5)
        )
        
        response = client.get(f"/api/v1/ai/study-plans/user/{test_user.id}")
        
        assert response.status_code == 200
        data = response.json()
        plans = data if isinstance(data, list) else data.get("items", data)
        assert len(plans) >= 2
        
        # 챌린지 플랜과 일반 플랜이 모두 포함되는지 확인
        challenge_plans = [p for p in plans if p["is_challenge"]]
        regular_plans = [p for p in plans if not p["is_challenge"]]
        assert len(challenge_plans) >= 1
        assert len(regular_plans) >= 1
    
    async def test_get_user_study_plans_with_filters(self, test_user):
        """필터를 사용한 사용자 스터디 플랜 목록 조회 API 테스트"""
        # 챌린지 플랜 생성
        await AIStudyPlan.create(
            user_id=test_user.id,
            is_challenge=True,
            input_data="Challenge 1",
            output_data="Challenge output 1",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30)
        )
        
        # 일반 플랜 생성
        await AIStudyPlan.create(
            user_id=test_user.id,
            is_challenge=False,
            input_data="Regular plan",
            output_data="Regular output",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=20)
        )
        
        # 챌린지 플랜만 조회
        response = client.get(f"/api/v1/ai/study-plans/user/{test_user.id}?is_challenge=true")
        
        assert response.status_code == 200
        data = response.json()
        plans = data if isinstance(data, list) else data.get("items", data)
        assert len(plans) >= 1
        for plan in plans:
            assert plan["is_challenge"] == True
            assert plan["user_id"] == test_user.id
    
    async def test_get_user_study_plans_nonexistent_user(self):
        """존재하지 않는 사용자의 스터디 플랜 조회 시 404 에러 테스트"""
        response = client.get("/api/v1/ai/study-plans/user/9999")
        assert response.status_code == 404
    
    async def test_update_study_plan_status(self, test_user, test_study_plan_data):
        """스터디 플랜 상태 업데이트 API 테스트"""
        test_study_plan_data["user_id"] = test_user.id
        
        create_response = client.post("/api/v1/ai/study-plans", json=test_study_plan_data)
        created_plan = create_response.json()
        plan_id = created_plan["id"]
        
        response = client.patch(f"/api/v1/ai/study-plans/{plan_id}/status?new_status=active")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == plan_id
    
    async def test_update_study_plan_status_invalid(self, test_user, test_study_plan_data):
        """잘못된 상태값으로 스터디 플랜 상태 업데이트 시 실패 테스트"""
        test_study_plan_data["user_id"] = test_user.id
        
        create_response = client.post("/api/v1/ai/study-plans", json=test_study_plan_data)
        created_plan = create_response.json()
        plan_id = created_plan["id"]
        
        response = client.patch(f"/api/v1/ai/study-plans/{plan_id}/status?new_status=invalid_status")
        
        assert response.status_code == 400
    
    async def test_get_user_plans_empty_results(self, test_user):
        """빈 결과 조회 테스트"""
        response = client.get(f"/api/v1/ai/study-plans/user/{test_user.id}?is_challenge=false")
        
        assert response.status_code == 200
        data = response.json()
        plans = data if isinstance(data, list) else data.get("items", data)
        assert isinstance(plans, list)