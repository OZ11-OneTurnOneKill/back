import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from tortoise.transactions import in_transaction

from app.services.ai_services.gemini_service import GeminiService
from app.models.ai import StudyPlan, ChallengeProgress
from app.dtos.ai.study_plan import StudyPlanRequest, StudyPlanResponse
from app.dtos.ai.challenge_progress import (
    ChallengeProgressResponse,
    StudyPlanWithChallengeResponse
)

logger = logging.getLogger(__name__)


class StudyPlanService:
    """학습계획 생성 및 관리 서비스"""

    def __init__(self, gemini_service: GeminiService):
        """서비스 초기화

        Args:
            gemini_service: Gemini API 연동 서비스
        """
        self.gemini_service = gemini_service

    async def create_study_plan(
            self,
            user_id: int,
            request: StudyPlanRequest
    ) -> StudyPlanWithChallengeResponse:
        """학습계획 생성 (챌린지 포함)

        Args:
            user_id: 사용자 ID
            request: 학습계획 요청 데이터

        Returns:
            생성된 학습계획 응답 (챌린지 정보 포함)

        Raises:
            Exception: AI 생성 실패 또는 DB 저장 실패
        """
        logger.info(f"Creating study plan for user {user_id} (challenge: {request.is_challenge})")

        try:
            # AI 학습계획 생성
            ai_response = await self.gemini_service.generate_study_plan(request)

            # ✅ 트랜잭션으로 StudyPlan과 ChallengeProgress 함께 생성
            async with in_transaction() as tx:
                # StudyPlan 생성
                study_plan = await StudyPlan.create(
                    user_id=user_id,
                    input_data=request.input_data,
                    output_data=json.dumps(ai_response, ensure_ascii=False),
                    is_challenge=request.is_challenge,
                    start_date=request.start_date,
                    end_date=request.end_date,
                    using_db=tx
                )

                challenge_progress = None

                # ✅ 챌린지 모드일 때 ChallengeProgress 생성
                if request.is_challenge:
                    challenge_progress = await ChallengeProgress.create(
                        study_plan_id=study_plan.id,
                        user_id=user_id,
                        status="진행 중",  # 초기 상태
                        challenge_image_url=None,  # 초기에는 이미지 없음
                        using_db=tx
                    )
                    logger.info(f"Challenge progress created with ID: {challenge_progress.id}")

            logger.info(f"Study plan created successfully with ID: {study_plan.id}")

            # ✅ 응답 스키마로 변환 (챌린지 정보 포함)
            challenge_response = None
            if challenge_progress:
                challenge_response = ChallengeProgressResponse(
                    id=challenge_progress.id,
                    study_plan_id=challenge_progress.study_plan_id,
                    user_id=challenge_progress.user_id,
                    status=challenge_progress.status,
                    challenge_image_url=challenge_progress.challenge_image_url,
                    created_at=challenge_progress.created_at,
                    updated_at=challenge_progress.updated_at
                )

            return StudyPlanWithChallengeResponse(
                id=study_plan.id,
                user_id=study_plan.user_id,
                input_data=study_plan.input_data,
                output_data=study_plan.output_data,
                is_challenge=study_plan.is_challenge,
                start_date=study_plan.start_date,
                end_date=study_plan.end_date,
                created_at=study_plan.created_at,
                challenge_progress=challenge_response
            )

        except Exception as e:
            logger.error(f"Failed to create study plan for user {user_id}: {str(e)}")
            raise e

    async def get_study_plan_with_challenge(
            self,
            study_plan_id: int,
            user_id: int
    ) -> StudyPlanWithChallengeResponse:
        """학습계획 조회 (챌린지 정보 포함)

        Args:
            study_plan_id: 학습계획 ID
            user_id: 사용자 ID (권한 검증용)

        Returns:
            학습계획 응답 (챌린지 정보 포함)

        Raises:
            ValueError: 계획이 존재하지 않거나 권한이 없는 경우
        """
        # DB에서 학습계획 조회
        study_plan = await StudyPlan.get_or_none(id=study_plan_id)

        if not study_plan:
            raise ValueError(f"Study plan not found: {study_plan_id}")

        # 사용자 권한 검증
        if study_plan.user_id != user_id:
            raise ValueError(f"Access denied for study plan {study_plan_id}")

        # 챌린지 정보 조회 (챌린지 모드인 경우)
        challenge_response = None
        if study_plan.is_challenge:
            challenge_progress = await ChallengeProgress.get_or_none(
                study_plan_id=study_plan_id,
                user_id=user_id
            )
            if challenge_progress:
                challenge_response = ChallengeProgressResponse(
                    id=challenge_progress.id,
                    study_plan_id=challenge_progress.study_plan_id,
                    user_id=challenge_progress.user_id,
                    status=challenge_progress.status,
                    challenge_image_url=challenge_progress.challenge_image_url,
                    created_at=challenge_progress.created_at,
                    updated_at=challenge_progress.updated_at
                )

        # 응답 스키마로 변환
        return StudyPlanWithChallengeResponse(
            id=study_plan.id,
            user_id=study_plan.user_id,
            input_data=study_plan.input_data,
            output_data=study_plan.output_data,
            is_challenge=study_plan.is_challenge,
            start_date=study_plan.start_date,
            end_date=study_plan.end_date,
            created_at=study_plan.created_at,
            challenge_progress=challenge_response
        )

    async def update_challenge_progress(
            self,
            study_plan_id: int,
            user_id: int,
            status: Optional[str] = None,
            challenge_image_url: Optional[str] = None
    ) -> ChallengeProgressResponse:
        """챌린지 진행상황 업데이트

        Args:
            study_plan_id: 학습계획 ID
            user_id: 사용자 ID
            status: 업데이트할 상태
            challenge_image_url: 업데이트할 이미지 URL

        Returns:
            업데이트된 챌린지 진행상황

        Raises:
            ValueError: 챌린지가 존재하지 않거나 권한이 없는 경우
        """
        # 챌린지 진행상황 조회
        challenge_progress = await ChallengeProgress.get_or_none(
            study_plan_id=study_plan_id,
            user_id=user_id
        )

        if not challenge_progress:
            raise ValueError(f"Challenge progress not found for study plan {study_plan_id}")

        # 필드 업데이트
        updated = False
        if status is not None:
            challenge_progress.status = status
            updated = True

        if challenge_image_url is not None:
            challenge_progress.challenge_image_url = challenge_image_url
            updated = True

        if updated:
            await challenge_progress.save()
            logger.info(f"Challenge progress {challenge_progress.id} updated successfully")

        # 응답 스키마로 변환
        return ChallengeProgressResponse(
            id=challenge_progress.id,
            study_plan_id=challenge_progress.study_plan_id,
            user_id=challenge_progress.user_id,
            status=challenge_progress.status,
            challenge_image_url=challenge_progress.challenge_image_url,
            created_at=challenge_progress.created_at,
            updated_at=challenge_progress.updated_at
        )

    async def get_study_plan_by_id(
            self,
            study_plan_id: int,
            user_id: int
    ) -> StudyPlanResponse:
        """학습계획 조회

        Args:
            study_plan_id: 학습계획 ID
            user_id: 사용자 ID (권한 검증용)

        Returns:
            학습계획 응답

        Raises:
            ValueError: 계획이 존재하지 않거나 권한이 없는 경우
        """
        # DB에서 학습계획 조회
        study_plan = await StudyPlan.get_or_none(id=study_plan_id)

        if not study_plan:
            raise ValueError(f"Study plan not found: {study_plan_id}")

        # 사용자 권한 검증
        if study_plan.user_id != user_id:
            raise ValueError(f"Access denied for study plan {study_plan_id}")

        # 응답 스키마로 변환
        return StudyPlanResponse(
            id=study_plan.id,
            user_id=study_plan.user_id,
            input_data=study_plan.input_data,
            output_data=study_plan.output_data,
            is_challenge=study_plan.is_challenge,
            start_date=study_plan.start_date,
            end_date=study_plan.end_date,
            created_at=study_plan.created_at
        )

    async def get_user_study_plans(
            self,
            user_id: int,
            limit: int = 10,
            offset: int = 0
    ) -> List[StudyPlanResponse]:
        """사용자의 학습계획 목록 조회

        Args:
            user_id: 사용자 ID
            limit: 조회 개수 제한
            offset: 건너뛸 개수

        Returns:
            학습계획 목록
        """
        study_plans = await StudyPlan.filter(user_id=user_id) \
            .order_by("-created_at") \
            .limit(limit).offset(offset)

        return [
            StudyPlanResponse(
                id=plan.id,
                user_id=plan.user_id,
                input_data=plan.input_data,
                output_data=plan.output_data,
                is_challenge=plan.is_challenge,
                start_date=plan.start_date,
                end_date=plan.end_date,
                created_at=plan.created_at
            )
            for plan in study_plans
        ]

    async def update_study_plan(
            self,
            study_plan_id: int,
            user_id: int,
            update_data: Dict[str, Any]
    ) -> StudyPlanResponse:
        """학습계획 업데이트

        Args:
            study_plan_id: 학습계획 ID
            user_id: 사용자 ID
            update_data: 업데이트할 데이터

        Returns:
            업데이트된 학습계획 응답

        Raises:
            ValueError: 계획이 존재하지 않거나 권한이 없는 경우
        """

        def convert_string_to_datetime(value: Union[str, datetime]) -> datetime:
            """문자열을 datetime 객체로 변환"""
            if isinstance(value, str):
                # ISO 형식 문자열을 datetime으로 변환
                if value.endswith('Z'):
                    value = value[:-1] + '+00:00'
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            return value

        # ✅ 디버깅: update_data 내용 확인
        logger.info(f"===== UPDATE DEBUG START =====")
        logger.info(f"Received update_data: {update_data}")
        logger.info(f"update_data type: {type(update_data)}")
        logger.info(f"update_data keys: {list(update_data.keys()) if isinstance(update_data, dict) else 'Not a dict'}")

        # ✅ 날짜 필드 변환
        if "start_date" in update_data and isinstance(update_data["start_date"], str):
            try:
                update_data["start_date"] = convert_string_to_datetime(update_data["start_date"])
                logger.info(f"✅ Converted start_date to datetime: {update_data['start_date']}")
            except Exception as e:
                logger.error(f"❌ Failed to convert start_date: {e}")
                raise ValueError(f"Invalid start_date format: {update_data['start_date']}")

        if "end_date" in update_data and isinstance(update_data["end_date"], str):
            try:
                update_data["end_date"] = convert_string_to_datetime(update_data["end_date"])
                logger.info(f"✅ Converted end_date to datetime: {update_data['end_date']}")
            except Exception as e:
                logger.error(f"❌ Failed to convert end_date: {e}")
                raise ValueError(f"Invalid end_date format: {update_data['end_date']}")

        # 기존 학습계획 조회 및 권한 검증
        study_plan = await StudyPlan.get_or_none(id=study_plan_id)

        if not study_plan:
            raise ValueError(f"Study plan not found: {study_plan_id}")

        if study_plan.user_id != user_id:
            raise ValueError(f"Access denied for study plan {study_plan_id}")

        try:
            # 입력 데이터가 변경된 경우 AI 재생성
            if "input_data" in update_data:
                logger.info(f"AI regeneration triggered for input_data change")
                # 업데이트된 요청 객체 생성
                updated_request = StudyPlanRequest(
                    input_data=update_data.get("input_data", study_plan.input_data),
                    start_date=update_data.get("start_date", study_plan.start_date),
                    end_date=update_data.get("end_date", study_plan.end_date),
                    is_challenge=update_data.get("is_challenge", study_plan.is_challenge)
                )

                # AI 학습계획 재생성
                ai_response = await self.gemini_service.generate_study_plan(updated_request)
                update_data["output_data"] = json.dumps(ai_response, ensure_ascii=False)

            # 개별 필드 업데이트
            updated = False

            logger.info(f"Before update - input_data: {study_plan.input_data}")
            logger.info(f"Before update - start_date: {study_plan.start_date}")
            logger.info(f"Before update - end_date: {study_plan.end_date}")
            logger.info(f"Before update - is_challenge: {study_plan.is_challenge}")

            # 각 필드를 개별적으로 업데이트
            if "input_data" in update_data:
                old_value = study_plan.input_data
                study_plan.input_data = update_data["input_data"]
                logger.info(f"✅ Updated input_data: '{old_value}' -> '{study_plan.input_data}'")
                updated = True

            if "output_data" in update_data:
                old_value = study_plan.output_data
                study_plan.output_data = update_data["output_data"]
                logger.info(
                    f"✅ Updated output_data: Changed (length: {len(str(old_value)) if old_value else 0} -> {len(str(study_plan.output_data))})")
                updated = True

            if "start_date" in update_data:
                old_value = study_plan.start_date
                study_plan.start_date = update_data["start_date"]
                logger.info(f"✅ Updated start_date: {old_value} -> {study_plan.start_date}")
                updated = True

            if "end_date" in update_data:
                old_value = study_plan.end_date
                study_plan.end_date = update_data["end_date"]
                logger.info(f"✅ Updated end_date: {old_value} -> {study_plan.end_date}")
                updated = True

            if "is_challenge" in update_data:
                old_value = study_plan.is_challenge
                study_plan.is_challenge = update_data["is_challenge"]
                logger.info(f"✅ Updated is_challenge: {old_value} -> {study_plan.is_challenge}")
                updated = True

            # 실제 변경사항이 있을 때만 저장
            if updated:
                logger.info(f"💾 Saving changes to database...")
                await study_plan.save()
                logger.info(f"✅ Study plan {study_plan_id} updated successfully")
            else:
                logger.warning(f"❌ No valid fields to update for study plan {study_plan_id}")

            # 업데이트된 엔티티 다시 조회
            updated_plan = await StudyPlan.get(id=study_plan_id)

            logger.info(f"After save - input_data: {updated_plan.input_data}")
            logger.info(f"===== UPDATE DEBUG END =====")

            # 응답 스키마로 변환
            return StudyPlanResponse(
                id=updated_plan.id,
                user_id=updated_plan.user_id,
                input_data=updated_plan.input_data,
                output_data=updated_plan.output_data,
                is_challenge=updated_plan.is_challenge,
                start_date=updated_plan.start_date,
                end_date=updated_plan.end_date,
                created_at=updated_plan.created_at
            )

        except Exception as e:
            logger.error(f"Failed to update study plan {study_plan_id}: {str(e)}")
            raise e

    async def delete_study_plan(
            self,
            study_plan_id: int,
            user_id: int
    ) -> None:
        """학습계획 삭제

        Args:
            study_plan_id: 학습계획 ID
            user_id: 사용자 ID

        Raises:
            ValueError: 계획이 존재하지 않거나 권한이 없는 경우
        """
        # 기존 학습계획 조회 및 권한 검증
        study_plan = await StudyPlan.get_or_none(id=study_plan_id)

        if not study_plan:
            raise ValueError(f"Study plan not found: {study_plan_id}")

        if study_plan.user_id != user_id:
            raise ValueError(f"Access denied for study plan {study_plan_id}")

        try:
            # DB에서 삭제
            await study_plan.delete()

            logger.info(f"Study plan {study_plan_id} deleted successfully")

        except Exception as e:
            logger.error(f"Failed to delete study plan {study_plan_id}: {str(e)}")
            raise e