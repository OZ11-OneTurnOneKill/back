from typing import List, Optional
from datetime import datetime, timedelta, timezone
from tortoise.exceptions import DoesNotExist, IntegrityError

from app.models.ai_study_plan import AIStudyPlan
from app.models.user import UserModel
from app.dtos.ai_study_plan.ai_study_plan_request import AIStudyPlanCreateRequest, AIStudyPlanUpdateRequest
from app.dtos.ai_study_plan.ai_study_plan_response import AIStudyPlanResponse, StudyPlanStatus
from app.utils.exceptions import (
    StudyPlanNotFoundError,
    UserNotFoundError,
    ValidationError,
    DatabaseError,
    DuplicateStudyPlanError,
    InvalidDateRangeError,
    InsufficientPermissionsError
)


class AIStudyPlanService:
    """AI 스터디 플랜 관련 비즈니스 로직을 처리하는 서비스 클래스"""

    @staticmethod
    async def create_study_plan(request: AIStudyPlanCreateRequest) -> AIStudyPlanResponse:
        """새로운 AI 스터디 플랜 생성
        
        Args:
            request: 스터디 플랜 생성 요청 데이터
            
        Returns:
            AIStudyPlanResponse: 생성된 스터디 플랜 응답 데이터
            
        Raises:
            InvalidDateRangeError: 시작일이 종료일보다 늦거나 같은 경우
            UserNotFoundError: 사용자가 존재하지 않는 경우
            DatabaseError: 데이터베이스 작업 실패
        """
        try:
            # 날짜 유효성 검증
            await AIStudyPlanService._validate_date_range(request.start_date, request.end_date)
            
            # 사용자 존재 여부 확인
            await AIStudyPlanService._validate_user_exists(request.user_id)
            
            # 스터디 플랜 생성
            study_plan = await AIStudyPlan.create(
                user_id=request.user_id,
                is_challenge=request.is_challenge,
                input_data=request.input_data,
                output_data="AI generated study plan will be added here",  # 임시 값
                start_date=request.start_date,
                end_date=request.end_date
            )
            
            return await AIStudyPlanService._convert_to_response(study_plan)
            
        except (InvalidDateRangeError, UserNotFoundError):
            raise
        except IntegrityError as e:
            raise DatabaseError(f"Database integrity error: {str(e)}", "create")
        except Exception as e:
            raise DatabaseError(f"Failed to create study plan: {str(e)}", "create")

    @staticmethod
    async def get_study_plans(
        user_id: Optional[int] = None,
        is_challenge: Optional[bool] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[AIStudyPlanResponse]:
        """스터디 플랜 목록 조회
        
        Args:
            user_id: 사용자 ID 필터 (선택사항)
            is_challenge: 챌린지 여부 필터 (선택사항)
            status: 상태 필터 (선택사항)
            limit: 최대 조회 개수 (기본값: 20)
            offset: 시작 위치 (기본값: 0)
            
        Returns:
            List[AIStudyPlanResponse]: 스터디 플랜 응답 리스트
            
        Raises:
            DatabaseError: 데이터베이스 조회 실패
        """
        try:
            # 쿼리 빌드
            query = AIStudyPlan.all().select_related('user')
            
            # 필터 적용
            if user_id is not None:
                query = query.filter(user_id=user_id)
            if is_challenge is not None:
                query = query.filter(is_challenge=is_challenge)
            
            # 페이징 적용
            study_plans = await query.offset(offset).limit(limit)
            
            # 응답 변환 및 상태 필터링
            responses = []
            for plan in study_plans:
                response = await AIStudyPlanService._convert_to_response(plan)
                if status and response.status != status:
                    continue
                responses.append(response)
            
            return responses
            
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve study plans: {str(e)}", "read")

    @staticmethod
    async def get_study_plan_by_id(plan_id: int) -> AIStudyPlanResponse:
        """특정 ID의 스터디 플랜 조회
        
        Args:
            plan_id: 스터디 플랜 ID
            
        Returns:
            AIStudyPlanResponse: 스터디 플랜 응답 데이터
            
        Raises:
            StudyPlanNotFoundError: 스터디 플랜을 찾을 수 없는 경우
            DatabaseError: 데이터베이스 조회 실패
        """
        try:
            study_plan = await AIStudyPlan.get_or_none(id=plan_id).select_related('user')
            if not study_plan:
                raise StudyPlanNotFoundError(plan_id)
            
            return await AIStudyPlanService._convert_to_response(study_plan)
            
        except StudyPlanNotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve study plan: {str(e)}", "read")

    @staticmethod
    async def update_study_plan(
        plan_id: int, 
        request: AIStudyPlanUpdateRequest
    ) -> AIStudyPlanResponse:
        """스터디 플랜 업데이트
        
        Args:
            plan_id: 스터디 플랜 ID
            request: 업데이트 요청 데이터
            
        Returns:
            AIStudyPlanResponse: 업데이트된 스터디 플랜 응답 데이터
            
        Raises:
            StudyPlanNotFoundError: 스터디 플랜을 찾을 수 없는 경우
            InvalidDateRangeError: 잘못된 날짜 범위
            DatabaseError: 데이터베이스 업데이트 실패
        """
        try:
            study_plan = await AIStudyPlan.get_or_none(id=plan_id)
            if not study_plan:
                raise StudyPlanNotFoundError(plan_id)
            
            # 업데이트 데이터 준비
            update_data = {}
            
            if request.input_data is not None:
                update_data['input_data'] = request.input_data
            if request.output_data is not None:
                update_data['output_data'] = request.output_data
            if request.start_date is not None:
                update_data['start_date'] = request.start_date
            if request.end_date is not None:
                update_data['end_date'] = request.end_date
            if request.is_challenge is not None:
                update_data['is_challenge'] = request.is_challenge
            
            # 날짜 유효성 검증
            if request.start_date or request.end_date:
                start_date = request.start_date or study_plan.start_date
                end_date = request.end_date or study_plan.end_date
                await AIStudyPlanService._validate_date_range(start_date, end_date)
            
            # 업데이트 수행
            if update_data:
                await study_plan.update_from_dict(update_data)
                await study_plan.save()
            
            return await AIStudyPlanService._convert_to_response(study_plan)
            
        except (StudyPlanNotFoundError, InvalidDateRangeError):
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to update study plan: {str(e)}", "update")

    @staticmethod
    async def delete_study_plan(plan_id: int) -> None:
        """스터디 플랜 삭제
        
        Args:
            plan_id: 스터디 플랜 ID
            
        Raises:
            StudyPlanNotFoundError: 스터디 플랜을 찾을 수 없는 경우
            DatabaseError: 데이터베이스 삭제 실패
        """
        try:
            study_plan = await AIStudyPlan.get_or_none(id=plan_id)
            if not study_plan:
                raise StudyPlanNotFoundError(plan_id)
            
            await study_plan.delete()
            
        except StudyPlanNotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to delete study plan: {str(e)}", "delete")

    @staticmethod
    async def get_user_study_plans(
        user_id: int,
        is_challenge: Optional[bool] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[AIStudyPlanResponse]:
        """특정 사용자의 스터디 플랜 목록 조회
        
        Args:
            user_id: 사용자 ID
            is_challenge: 챌린지 여부 필터 (선택사항)
            status: 상태 필터 (선택사항)
            limit: 최대 조회 개수 (기본값: 20)
            offset: 시작 위치 (기본값: 0)
            
        Returns:
            List[AIStudyPlanResponse]: 스터디 플랜 응답 리스트
            
        Raises:
            UserNotFoundError: 사용자를 찾을 수 없는 경우
            DatabaseError: 데이터베이스 조회 실패
        """
        try:
            # 사용자 존재 여부 확인
            await AIStudyPlanService._validate_user_exists(user_id)
            
            # 일반 조회 메서드 사용
            return await AIStudyPlanService.get_study_plans(
                user_id=user_id,
                is_challenge=is_challenge,
                status=status,
                limit=limit,
                offset=offset
            )
            
        except UserNotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve user study plans: {str(e)}", "read")

    @staticmethod
    async def update_study_plan_status(plan_id: int, new_status: str) -> AIStudyPlanResponse:
        """스터디 플랜 상태 업데이트
        
        Args:
            plan_id: 스터디 플랜 ID
            new_status: 새로운 상태값
            
        Returns:
            AIStudyPlanResponse: 업데이트된 스터디 플랜 응답 데이터
            
        Raises:
            StudyPlanNotFoundError: 스터디 플랜을 찾을 수 없는 경우
            ValidationError: 잘못된 상태값
            DatabaseError: 데이터베이스 업데이트 실패
        """
        try:
            study_plan = await AIStudyPlan.get_or_none(id=plan_id)
            if not study_plan:
                raise StudyPlanNotFoundError(plan_id)
            
            # 상태값 유효성 검증
            try:
                StudyPlanStatus(new_status)
            except ValueError:
                raise ValidationError(f"Invalid status: {new_status}")
            
            # 현재는 상태를 직접 저장하지 않고 계산된 상태만 반환
            # 향후 확장 시 여기에 상태 저장 로직 추가 가능
            
            return await AIStudyPlanService._convert_to_response(study_plan)
            
        except (StudyPlanNotFoundError, ValidationError):
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to update study plan status: {str(e)}", "update")

    @staticmethod
    async def get_user_statistics(user_id: int) -> dict:
        """사용자의 스터디 플랜 통계 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            dict: 사용자 통계 데이터
            
        Raises:
            UserNotFoundError: 사용자를 찾을 수 없는 경우
            DatabaseError: 데이터베이스 조회 실패
        """
        try:
            # 사용자 존재 여부 확인
            await AIStudyPlanService._validate_user_exists(user_id)
            
            # 모든 스터디 플랜 조회
            all_plans = await AIStudyPlan.filter(user_id=user_id)
            
            # 통계 계산
            total_plans = len(all_plans)
            challenge_plans = len([p for p in all_plans if p.is_challenge])
            
            current_time = datetime.now()
            norm_current = AIStudyPlanService._normalize_datetime(current_time)
            
            active_plans = len([
                p for p in all_plans 
                if AIStudyPlanService._normalize_datetime(p.start_date) <= norm_current <= AIStudyPlanService._normalize_datetime(p.end_date)
            ])
            completed_plans = len([
                p for p in all_plans 
                if AIStudyPlanService._normalize_datetime(p.end_date) < norm_current
            ])
            
            return {
                "user_id": user_id,
                "total_plans": total_plans,
                "challenge_plans": challenge_plans,
                "active_plans": active_plans,
                "completed_plans": completed_plans,
                "completion_rate": (completed_plans / total_plans * 100) if total_plans > 0 else 0,
                "average_plan_duration": AIStudyPlanService._calculate_average_duration(all_plans)
            }
            
        except UserNotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve user statistics: {str(e)}", "read")

    # Private helper methods

    @staticmethod
    def _normalize_datetime(dt: datetime) -> datetime:
        """Normalize datetime to handle timezone comparisons consistently"""
        if not isinstance(dt, datetime):
            raise TypeError(f"Expected datetime object, got {type(dt)}")
        if dt.tzinfo is None:
            # If naive, assume it's in local timezone
            return dt.replace(tzinfo=timezone.utc)
        return dt

    @staticmethod
    async def _validate_user_exists(user_id: int) -> None:
        """사용자 존재 여부 검증"""
        user = await UserModel.get_or_none(id=user_id)
        if not user:
            raise UserNotFoundError(user_id)

    @staticmethod
    async def _validate_date_range(start_date: datetime, end_date: datetime) -> None:
        """날짜 범위 유효성 검증"""
        # Normalize datetimes for consistent comparison
        norm_start = AIStudyPlanService._normalize_datetime(start_date)
        norm_end = AIStudyPlanService._normalize_datetime(end_date)
        
        if norm_start >= norm_end:
            raise InvalidDateRangeError()

    @staticmethod
    async def _convert_to_response(study_plan: AIStudyPlan) -> AIStudyPlanResponse:
        """스터디 플랜 모델을 응답 DTO로 변환"""
        now = datetime.now()
        
        # Normalize all datetimes for consistent comparisons
        norm_now = AIStudyPlanService._normalize_datetime(now)
        norm_start = AIStudyPlanService._normalize_datetime(study_plan.start_date)
        norm_end = AIStudyPlanService._normalize_datetime(study_plan.end_date)
        
        # 활성 상태 계산
        is_active = norm_start <= norm_now <= norm_end
        
        # 진행률 계산
        total_days = (norm_end - norm_start).days
        if total_days > 0:
            elapsed_days = max(0, (norm_now - norm_start).days)
            progress_percentage = min(100, int((elapsed_days / total_days) * 100))
        else:
            progress_percentage = 0 if norm_now < norm_start else 100
        
        # 남은 일수 계산
        days_remaining = (norm_end - norm_now).days
        
        # 상태 결정
        status = AIStudyPlanService._calculate_status(study_plan, now)
        
        return AIStudyPlanResponse(
            id=study_plan.id,
            user_id=study_plan.user_id,
            is_challenge=study_plan.is_challenge,
            input_data=study_plan.input_data,
            output_data=getattr(study_plan, 'output_data', ''),
            start_date=study_plan.start_date,
            end_date=study_plan.end_date,
            status=status,
            created_at=study_plan.created_at,
            updated_at=study_plan.updated_at,
            is_active=is_active,
            progress_percentage=progress_percentage,
            days_remaining=days_remaining
        )

    @staticmethod
    def _calculate_status(study_plan: AIStudyPlan, now: datetime) -> StudyPlanStatus:
        """스터디 플랜 상태 계산"""
        # Normalize datetimes for consistent comparison
        norm_now = AIStudyPlanService._normalize_datetime(now)
        norm_start = AIStudyPlanService._normalize_datetime(study_plan.start_date)
        norm_end = AIStudyPlanService._normalize_datetime(study_plan.end_date)
        
        if norm_now > norm_end:
            return StudyPlanStatus.COMPLETED
        elif norm_now >= norm_start:
            return StudyPlanStatus.ACTIVE
        else:
            return StudyPlanStatus.PLANNED

    @staticmethod
    def _calculate_average_duration(study_plans: List[AIStudyPlan]) -> float:
        """평균 스터디 플랜 기간 계산 (일 단위)"""
        if not study_plans:
            return 0.0
        
        total_duration = sum([
            (plan.end_date - plan.start_date).days 
            for plan in study_plans
        ])
        
        return round(total_duration / len(study_plans), 2)


# 기존 클래스명과의 하위 호환성을 위한 별칭
AIService = AIStudyPlanService