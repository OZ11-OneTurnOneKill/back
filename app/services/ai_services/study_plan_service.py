import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.ai_services.gemini_service import GeminiService
from app.models.ai import StudyPlan
from app.dtos.ai_study_plan.study_plan import StudyPlanRequest, StudyPlanResponse, StudyPlanUpdate

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
    ) -> StudyPlanResponse:
        """학습계획 생성

        Args:
            user_id: 사용자 ID
            request: 학습계획 요청 데이터

        Returns:
            생성된 학습계획 응답

        Raises:
            Exception: AI 생성 실패 또는 DB 저장 실패
        """
        logger.info(f"Creating study plan for user {user_id}")

        try:
            # AI 학습계획 생성
            ai_response = await self.gemini_service.generate_study_plan(request)

            # DB에 저장할 StudyPlan 엔티티 생성
            study_plan = await StudyPlan.create(
                user_id=user_id,
                input_data=request.input_data,
                output_data=json.dumps(ai_response, ensure_ascii=False),
                is_challenge=request.is_challenge,
                start_date=request.start_date,
                end_date=request.end_date
            )

            logger.info(f"Study plan created successfully with ID: {study_plan.id}")

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

        except Exception as e:
            logger.error(f"Failed to create study plan for user {user_id}: {str(e)}")
            raise e

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
        # 기존 학습계획 조회 및 권한 검증
        study_plan = await StudyPlan.get_or_none(id=study_plan_id)

        if not study_plan:
            raise ValueError(f"Study plan not found: {study_plan_id}")

        if study_plan.user_id != user_id:
            raise ValueError(f"Access denied for study plan {study_plan_id}")

        try:
            # 입력 데이터가 변경된 경우 AI 재생성
            if "input_data" in update_data:
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

            # 필드 업데이트
            await study_plan.update_from_dict(update_data).save()

            logger.info(f"Study plan {study_plan_id} updated successfully")

            # 업데이트된 엔티티 다시 조회
            updated_plan = await StudyPlan.get(id=study_plan_id)

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