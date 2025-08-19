import json
import logging
from typing import Dict, Any, Optional, List
from app.exceptions.study_plan_exception import StudyPlanNotFoundError, StudyPlanAccessDeniedError
from app.services.ai_services.gemini_service import GeminiService
from app.models.ai import DocumentSummary
from app.dtos.ai.summary import SummaryRequest, SummaryResponse

logger = logging.getLogger(__name__)


class SummaryService:
    """자료 요약 서비스 - 단순화 및 구조 정리"""

    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service

    async def create_summary(
            self,
            user_id: int,
            request: SummaryRequest
    ) -> SummaryResponse:
        """자료 요약 생성 - 단순화된 버전"""
        logger.info(f"Creating summary for user {user_id}")

        try:
            # SummaryRequest의 validator에서 이미 텍스트가 정리되었으므로
            # 추가 전처리 없이 바로 Gemini 서비스 호출
            logger.info(f"처리할 텍스트 길이: {len(request.input_data)}")
            logger.info(f"텍스트 미리보기: {request.input_data[:100]}...")

            # GeminiService를 통해 요약 생성
            ai_response = await self.gemini_service.generate_summary(
                content=request.input_data,  # 이미 validator에서 정리된 텍스트
                summary_type=request.summary_type,
                title=request.title
            )

            logger.info(f"AI 응답 받음: {type(ai_response)}")

            # DB에 저장
            summary = await DocumentSummary.create(
                user_id=user_id,
                title=request.title,
                input_type=request.input_type,
                input_data=request.input_data,
                summary_type=request.summary_type,
                output_data=json.dumps(ai_response, ensure_ascii=False),
                file_url=request.file_url
            )

            logger.info(f"Summary created successfully with ID: {summary.id}")

            return SummaryResponse(
                id=summary.id,
                user_id=summary.user_id,
                title=summary.title,
                input_type=summary.input_type,
                input_data=summary.input_data,
                summary_type=summary.summary_type,
                output_data=summary.output_data,
                file_url=summary.file_url,
                created_at=summary.created_at
            )

        except Exception as e:
            logger.error(f"Failed to create summary for user {user_id}: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise e

    async def get_user_summaries(
            self,
            user_id: int,
            limit: int = 10,
            offset: int = 0
    ) -> List[SummaryResponse]:
        """사용자별 요약 목록 조회"""
        summaries = await DocumentSummary.filter(user_id=user_id) \
            .order_by("-created_at") \
            .limit(limit).offset(offset)

        return [
            SummaryResponse(
                id=summary.id,
                user_id=summary.user_id,
                title=summary.title,
                input_type=summary.input_type,
                input_data=summary.input_data,
                summary_type=summary.summary_type,
                output_data=summary.output_data,
                file_url=summary.file_url,
                created_at=summary.created_at
            )
            for summary in summaries
        ]

    async def delete_summary(
            self,
            summary_id: int,
            user_id: int
    ) -> None:
        """자료 요약 삭제"""
        logger.info(f"Deleting summary {summary_id} for user {user_id}")

        # 삭제할 요약 조회
        summary = await DocumentSummary.get_or_none(id=summary_id)

        # 존재 여부 확인
        if not summary:
            logger.warning(f"Summary not found: {summary_id}")
            raise StudyPlanNotFoundError(summary_id)

        # 권한 검증
        if summary.user_id != user_id:
            logger.warning(
                f"Access denied: User {user_id} tried to delete summary {summary_id} owned by user {summary.user_id}")
            raise StudyPlanAccessDeniedError(summary_id, user_id)

        try:
            await summary.delete()
            logger.info(f"Summary {summary_id} deleted successfully by user {user_id}")
        except Exception as e:
            logger.error(f"Failed to delete summary {summary_id}: {str(e)}")
            raise e

    async def get_summary_by_id(
            self,
            summary_id: int,
            user_id: int
    ) -> SummaryResponse:
        """특정 요약 조회"""
        summary = await DocumentSummary.get_or_none(id=summary_id)

        if not summary:
            raise StudyPlanNotFoundError(summary_id)

        if summary.user_id != user_id:
            raise StudyPlanAccessDeniedError(summary_id, user_id)

        return SummaryResponse(
            id=summary.id,
            user_id=summary.user_id,
            title=summary.title,
            input_type=summary.input_type,
            input_data=summary.input_data,
            summary_type=summary.summary_type,
            output_data=summary.output_data,
            file_url=summary.file_url,
            created_at=summary.created_at
        )