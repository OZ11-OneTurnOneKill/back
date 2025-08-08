# AI 학습계획 데이터베이스 모델 테스트를 위한 라이브러리 임포트
import pytest  # 테스트 프레임워크
import pytest_asyncio
from datetime import datetime, timedelta, timezone  # 날짜/시간 처리용
from tortoise import Tortoise  # Tortoise ORM 직접 사용
from app.models.ai_study_plan import AIStudyPlan  # AI 학습계획 모델
from app.models.user import UserModel, SocialAccountModel, ProviderType  # 사용자 모델

# 테스트 데이터베이스 초기화 및 정리 fixture
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

# 모델 테스트용 사용자 생성 fixture
@pytest_asyncio.fixture
async def test_user():
    """AI 모델 테스트에 사용할 사용자 계정을 생성"""
    # Google 소셜 계정 생성
    social_account = await SocialAccountModel.create(
        provider=ProviderType.GOOGLE,
        provider_id="test_model_123",
        email="model@example.com"
    )
    # 소셜 계정과 연결된 사용자 생성
    user = await UserModel.create(
        social_account=social_account,
        nickname="modltest",
        profile_image_url="https://example.com/model.jpg"
    )
    return user


@pytest_asyncio.fixture(autouse=True)
async def cleanup_data():
    """Clean up test data after each test"""
    yield
    # Clean up in reverse dependency order
    await AIStudyPlan.all().delete()
    await UserModel.all().delete()
    await SocialAccountModel.all().delete()


# Helper function for timezone-aware datetime normalization
def normalize_datetime(dt):
    """Convert naive datetime to timezone-aware for comparison"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# AI 학습계획 데이터베이스 모델의 직접적인 CRUD 작업 테스트 클래스
@pytest.mark.asyncio
class TestAIStudyPlanModel:
    """AIStudyPlan 모델의 데이터베이스 직접 작업 (API 없이 모델만 테스트)"""
    
    async def test_create_study_plan_model(self, test_user):
        """AIStudyPlan 모델의 기본 생성 작업 테스트"""
        # 테스트용 학습계획 날짜 설정
        start_date = datetime.now()  # 현재 시간을 시작일로 설정
        end_date = start_date + timedelta(days=30)  # 30일 후를 종료일로 설정
        
        # Tortoise ORM을 통해 직접 AIStudyPlan 모델 인스턴스 생성
        study_plan = await AIStudyPlan.create(
            user_id=test_user.id,  # 테스트 사용자 ID
            is_challenge=False,  # 일반 학습계획 (챌린지 아님)
            input_data="Learn Django in 30 days",  # 사용자 입력 프롬프트
            output_data="Week 1: Django basics\nWeek 2: Models and ORM\nWeek 3: Views and Templates\nWeek 4: REST APIs",  # AI 생성 계획
            start_date=start_date,  # 학습 시작일
            end_date=end_date  # 학습 종료일
        )
        
        # 생성된 모델 인스턴스의 모든 필드 값 검증
        assert study_plan.id is not None  # 자동 생성된 고유 ID가 있는지 확인
        assert study_plan.user_id == test_user.id  # 사용자 ID가 올바르게 설정되었는지 확인
        assert study_plan.is_challenge == False  # 챌린지 여부가 올바르게 설정되었는지 확인
        assert study_plan.input_data == "Learn Django in 30 days"  # 입력 데이터 일치 확인
        assert study_plan.output_data == "Week 1: Django basics\nWeek 2: Models and ORM\nWeek 3: Views and Templates\nWeek 4: REST APIs"  # 출력 데이터 일치 확인
        assert normalize_datetime(study_plan.start_date) == normalize_datetime(start_date)  # 시작일 일치 확인
        assert normalize_datetime(study_plan.end_date) == normalize_datetime(end_date)  # 종료일 일치 확인
        assert study_plan.created_at is not None  # BaseModel의 created_at 자동 생성 확인
        assert study_plan.updated_at is not None  # BaseModel의 updated_at 자동 생성 확인
    
    async def test_create_challenge_study_plan(self, test_user):
        """챌린지 모드 학습계획 모델 생성 테스트 (is_challenge=True)"""
        start_date = datetime.now()  # 시작일 설정
        end_date = start_date + timedelta(days=14)  # 2주 챌린지 기간
        
        # 챌린지 모드로 학습계획 생성
        challenge_plan = await AIStudyPlan.create(
            user_id=test_user.id,
            is_challenge=True,  # 챌린지 모드 활성화
            input_data="2-week coding challenge",  # 챌린지 내용
            output_data="Daily coding exercises focusing on algorithms and data structures",  # 챌린지 계획
            start_date=start_date,
            end_date=end_date
        )
        
        # 챌린지 계획 생성 결과 검증
        assert challenge_plan.is_challenge == True  # 챌린지 모드가 올바르게 설정되었는지 확인
        assert challenge_plan.user_id == test_user.id  # 사용자 ID 확인
        assert "challenge" in challenge_plan.input_data.lower()  # 입력 데이터에 'challenge' 단어가 포함되어 있는지 확인
    
    async def test_study_plan_relationships(self, test_user):
        """학습계획과 사용자 모델 간의 관계 테스트 (Foreign Key 관계)"""
        # 테스트용 학습계획 생성
        study_plan = await AIStudyPlan.create(
            user_id=test_user.id,
            is_challenge=False,
            input_data="Test relationship",
            output_data="Test output",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=10)
        )
        
        # select_related를 사용하여 사용자 정보와 함께 조회 (관계 테스트)
        retrieved_plan = await AIStudyPlan.get(id=study_plan.id).select_related('user')
        assert retrieved_plan.user_id == test_user.id  # Foreign Key 관계가 올바르게 설정되었는지 확인
    
    async def test_study_plan_filtering(self, test_user):
        """데이터베이스 필터링 기능 테스트 (사용자별, 챌린지 여부별 필터링)"""
        # 테스트용 챌린지 계획 생성
        await AIStudyPlan.create(
            user_id=test_user.id,
            is_challenge=True,  # 챌린지 계획
            input_data="Challenge 1",
            output_data="Challenge output 1",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30)
        )
        
        # 테스트용 일반 계획 생성
        await AIStudyPlan.create(
            user_id=test_user.id,
            is_challenge=False,  # 일반 계획
            input_data="Regular plan 1",
            output_data="Regular output 1",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=20)
        )
        
        # 챌린지 계획만 필터링하여 조회
        challenge_plans = await AIStudyPlan.filter(
            user_id=test_user.id,  # 특정 사용자의 계획만
            is_challenge=True      # 챌린지 계획만
        )
        assert len(challenge_plans) == 1  # 챌린지 계획이 정확히 1개 조회되는지 확인
        assert challenge_plans[0].is_challenge == True  # 조회된 계획이 챌린지인지 확인
        
        # 일반 계획만 필터링하여 조회
        regular_plans = await AIStudyPlan.filter(
            user_id=test_user.id,  # 특정 사용자의 계획만
            is_challenge=False     # 일반 계획만
        )
        assert len(regular_plans) >= 1  # 최소 1개의 일반 계획이 있어야 함
        # 모든 조회된 계획이 일반 계획인지 확인
        for plan in regular_plans:
            assert plan.is_challenge == False  # 각 계획이 일반 계획인지 확인
    
    async def test_study_plan_date_filtering(self, test_user):
        """날짜 기반 필터링 테스트 (활성 상태인 학습계획 조회)"""
        current_time = datetime.now()  # 현재 시간 기준
        
        # 현재 활성 상태인 학습계획 생성 (종료일이 미래)
        await AIStudyPlan.create(
            user_id=test_user.id,
            is_challenge=False,
            input_data="Active plan",
            output_data="Active output",
            start_date=current_time - timedelta(days=5),  # 5일 전에 시작
            end_date=current_time + timedelta(days=25)    # 25일 후에 종료 (활성)
        )
        
        # 이미 만료된 학습계획 생성 (종료일이 과거)
        await AIStudyPlan.create(
            user_id=test_user.id,
            is_challenge=False,
            input_data="Expired plan",
            output_data="Expired output",
            start_date=current_time - timedelta(days=60),  # 60일 전에 시작
            end_date=current_time - timedelta(days=30)     # 30일 전에 종료 (만료)
        )
        
        # 날짜 필터링을 사용하여 활성 계획만 조회 (end_date__gt: 종료일이 현재보다 큰 것)
        active_plans = await AIStudyPlan.filter(
            user_id=test_user.id,
            end_date__gt=current_time  # Tortoise ORM 날짜 필터 문법 (종료일 > 현재 시간)
        )
        
        # 활성 계획 조회 결과 검증
        assert len(active_plans) >= 1  # 최소 1개의 활성 계획이 있어야 함
        # 모든 조회된 계획의 종료일이 현재보다 미래인지 확인
        for plan in active_plans:
            assert normalize_datetime(plan.end_date) > normalize_datetime(current_time)  # 각 계획의 종료일이 현재보다 미래인지 확인
    
    async def test_study_plan_update(self, test_user):
        """학습계획 모델 업데이트 기능 테스트 (updated_at 자동 업데이트 포함)"""
        # 업데이트할 학습계획 생성
        study_plan = await AIStudyPlan.create(
            user_id=test_user.id,
            is_challenge=False,
            input_data="Original input",  # 원본 입력 데이터
            output_data="Original output",  # 원본 출력 데이터
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30)
        )
        
        # 업데이트 전 updated_at 시간 저장 (비교용)
        original_updated_at = study_plan.updated_at
        
        # 모델 인스턴스의 필드 직접 수정
        study_plan.input_data = "Updated input"  # 입력 데이터 업데이트
        study_plan.output_data = "Updated output"  # 출력 데이터 업데이트
        study_plan.is_challenge = True  # 챌린지 모드로 변경
        await study_plan.save()  # 데이터베이스에 변경사항 저장
        
        # 데이터베이스에서 다시 조회하여 업데이트 결과 검증
        updated_plan = await AIStudyPlan.get(id=study_plan.id)
        assert updated_plan.input_data == "Updated input"  # 입력 데이터 업데이트 확인
        assert updated_plan.output_data == "Updated output"  # 출력 데이터 업데이트 확인
        assert updated_plan.is_challenge == True  # 챌린지 모드 변경 확인
        assert updated_plan.updated_at > original_updated_at  # BaseModel의 updated_at이 자동 업데이트되었는지 확인
    
    async def test_study_plan_delete(self, test_user):
        """학습계획 모델 삭제 기능 테스트 (삭제 후 조회 불가능 확인)"""
        # 삭제할 학습계획 생성
        study_plan = await AIStudyPlan.create(
            user_id=test_user.id,
            is_challenge=False,
            input_data="To be deleted",  # 삭제될 데이터
            output_data="Delete this plan",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=10)
        )
        
        # 삭제 전 ID 저장 (나중에 조회를 위해)
        plan_id = study_plan.id
        # 모델 인스턴스 삭제
        await study_plan.delete()
        
        # 삭제된 모델을 다시 조회 시도 (get_or_none은 없으면 None 반환)
        deleted_plan = await AIStudyPlan.get_or_none(id=plan_id)
        assert deleted_plan is None  # 삭제되어 None이 반환되는지 확인
    
    async def test_study_plan_bulk_operations(self, test_user):
        """대량 데이터 생성 및 개수 카운팅 테스트 (챌린지/일반 계획 비율 확인)"""
        # 테스트용 대량 데이터 준비 (5개의 학습계획)
        plans_data = [
            {
                "user_id": test_user.id,
                "is_challenge": i % 2 == 0,  # 짝수 인덱스는 챌린지, 홀수는 일반 (0,2,4=챌린지 / 1,3=일반)
                "input_data": f"Bulk plan {i}",  # 각각 다른 입력 데이터
                "output_data": f"Bulk output {i}",  # 각각 다른 출력 데이터
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=30)
            }
            for i in range(5)  # 0부터 4까지 5개 데이터 생성
        ]
        
        # 준비된 데이터로 학습계획 일괄 생성
        created_plans = []
        for plan_data in plans_data:
            plan = await AIStudyPlan.create(**plan_data)  # 딕셔너리 언팩킹으로 모델 생성
            created_plans.append(plan)
        
        # 생성된 계획 수 확인
        assert len(created_plans) == 5  # 정확히 5개가 생성되었는지 확인
        
        # 데이터베이스에서 해당 사용자의 모든 계획 조회
        user_plans = await AIStudyPlan.filter(user_id=test_user.id)
        assert len(user_plans) >= 5  # 최소 5개 이상의 계획이 있어야 함 (다른 테스트에서 생성한 것들도 포함)
        
        # 챌린지 계획 개수 카운트 (count() 메서드 활용)
        challenge_count = await AIStudyPlan.filter(
            user_id=test_user.id,
            is_challenge=True
        ).count()
        # 일반 계획 개수 카운트
        regular_count = await AIStudyPlan.filter(
            user_id=test_user.id,
            is_challenge=False
        ).count()
        
        # 예상되는 챌린지/일반 계획 비율 검증 (i%2==0이므로 3개 챌린지, 2개 일반)
        assert challenge_count >= 3  # 최소 3개 이상의 챌린지 계획 (0,2,4)
        assert regular_count >= 2  # 최소 2개 이상의 일반 계획 (1,3)
    
    async def test_study_plan_ordering(self, test_user):
        """데이터베이스 정렬 기능 테스트 (오름차순/내림차순 정렬)"""
        base_time = datetime.now()  # 기준 시간 설정
        
        # 시간 간격을 두고 3개의 학습계획 생성 (생성 시간이 다르도록)
        for i in range(3):
            await AIStudyPlan.create(
                user_id=test_user.id,
                is_challenge=False,
                input_data=f"Plan {i}",  # 각각 다른 계획 이름
                output_data=f"Output {i}",
                start_date=base_time + timedelta(hours=i),  # 시간별로 다른 시작일
                end_date=base_time + timedelta(days=30, hours=i)  # 시간별로 다른 종료일
            )
        
        # 오름차순 정렬 (created_at 기준 오래된 것부터)
        plans_asc = await AIStudyPlan.filter(
            user_id=test_user.id
        ).order_by('created_at')  # 오름차순
        
        # 내림차순 정렬 (created_at 기준 최신 것부터, '-' 사용)
        plans_desc = await AIStudyPlan.filter(
            user_id=test_user.id
        ).order_by('-created_at')  # 내림차순
        
        # 정렬 결과 검증
        assert len(plans_asc) >= 3  # 오름차순 결과에 최소 3개 이상이 있는지 확인
        assert len(plans_desc) >= 3  # 내림차순 결과에 최소 3개 이상이 있는지 확인
        # 오름차순: 첫 번째 항목의 created_at <= 마지막 항목의 created_at
        assert plans_asc[0].created_at <= plans_asc[-1].created_at
        # 내림차순: 첫 번째 항목의 created_at >= 마지막 항목의 created_at
        assert plans_desc[0].created_at >= plans_desc[-1].created_at