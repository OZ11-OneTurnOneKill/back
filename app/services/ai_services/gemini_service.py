import json
from google import generativeai as genai
from typing import Dict, Any
from datetime import datetime
from app.dtos.ai_study_plan.study_plan import StudyPlanRequest

import logging
import json

logger = logging.getLogger(__name__)


class GeminiService:
    """Gemini API 연동 서비스"""

    def __init__(self, api_key: str):
        """Gemini 서비스 초기화

        Args:
            api_key: Gemini API 키
        """
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    # gemini_service.py의 generate_study_plan 메서드에 추가


    async def generate_study_plan(self, request) -> Dict[str, Any]:
        """디버깅이 추가된 학습계획 생성"""
        try:
            logger.info(f"🔍 API 키 확인: {self.api_key[:10]}..." if self.api_key else "❌ API 키 없음")

            prompt = self._build_prompt(request)
            logger.info(f"📝 프롬프트 생성 완료: {len(prompt)} 문자")

            # Gemini API 호출
            response = await self.model.generate_content_async(prompt)
            logger.info(f"📨 Gemini 응답 받음: {len(response.text)} 문자")

            # 🔥 실제 응답 내용 로깅 (문제 파악용)
            logger.info(f"📄 실제 응답 내용: {response.text[:500]}...")

            # JSON 파싱 시도
            try:
                # 간단한 정리 후 파싱
                clean_text = response.text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:-3]
                elif clean_text.startswith("```"):
                    clean_text = clean_text[3:-3]

                logger.info(f"🧹 정리된 텍스트: {clean_text[:200]}...")

                parsed_response = json.loads(clean_text)
                logger.info("✅ JSON 파싱 성공!")

                return parsed_response

            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON 파싱 실패: {e}")
                logger.error(f"❌ 파싱 실패 원본: {response.text}")

                # 🔥 임시 해결: 기본 응답 반환
                return {
                    "title": f"{request.input_data} 학습계획",
                    "total_weeks": 4,
                    "difficulty": "beginner",
                    "weekly_plans": [
                        {
                            "week": 1,
                            "title": "1주차: 기초 학습",
                            "topics": ["기본 개념", "실습"],
                            "goals": ["기초 이해"],
                            "estimated_hours": 8
                        }
                    ],
                    "milestones": [{"week": 4, "milestone": "완료"}],
                    "_fallback": True
                }

        except Exception as e:
            logger.error(f"❌ Gemini API 호출 전체 실패: {e}")
            raise ValueError(f"Gemini API error: {str(e)}")


    def _build_prompt(self, request: StudyPlanRequest) -> str:
        """학습계획 생성 프롬프트 구성

        Args:
            request: 학습계획 요청 데이터

        Returns:
            구성된 프롬프트 문자열
        """
        # 학습 기간 계산
        duration_days = (request.end_date - request.start_date).days
        duration_weeks = max(1, duration_days // 7)

        # 챌린지 모드 여부에 따른 추가 지침
        challenge_instruction = ""
        if request.is_challenge:
            challenge_instruction = """
이것은 집중 챌린지 모드입니다. 다음 사항을 고려해주세요:
- 더 집중적이고 강도 높은 학습 계획
- 명확한 일일 목표와 체크포인트
- 동기부여를 위한 중간 성취 지표
"""

        prompt = f"""
사용자 요청: {request.input_data}

학습 기간: {request.start_date.strftime('%Y-%m-%d')} ~ {request.end_date.strftime('%Y-%m-%d')} (총 {duration_days}일, 약 {duration_weeks}주)

{challenge_instruction}

다음 JSON 형식으로 상세한 학습계획을 작성해주세요:

{{
    "title": "학습계획 제목",
    "total_weeks": {duration_weeks},
    "difficulty": "beginner|intermediate|advanced|beginner_to_advanced",
    "weekly_plans": [
        {{
            "week": 1,
            "title": "주차별 제목",
            "topics": ["학습 주제1", "학습 주제2"],
            "goals": ["달성 목표1", "달성 목표2"],
            "estimated_hours": 10
        }}
    ],
    "milestones": [
        {{
            "week": 4,
            "milestone": "중간 목표 설명"
        }}
    ]
}}

주의사항:
1. weekly_plans는 정확히 {duration_weeks}개의 주차 계획을 포함해야 합니다
2. 각 주차별로 구체적이고 실행 가능한 학습 목표를 제시해주세요
3. 난이도는 점진적으로 증가하도록 구성해주세요
4. 실제 학습 가능한 시간을 고려해주세요
5. JSON 형식을 정확히 지켜주세요 (코드 블록 없이 순수 JSON만)
"""

        return prompt

    def _validate_response_structure(self, response: Dict[str, Any]) -> None:
        """AI 응답 구조 검증

        Args:
            response: AI 응답 데이터

        Raises:
            ValueError: 필수 필드 누락 시
        """
        required_fields = ["title", "total_weeks", "weekly_plans", "milestones"]
        missing_fields = [field for field in required_fields if field not in response]

        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # weekly_plans 구조 검증
        if not isinstance(response["weekly_plans"], list):
            raise ValueError("weekly_plans must be a list")

        for i, week_plan in enumerate(response["weekly_plans"]):
            week_required_fields = ["week", "title", "topics", "goals"]
            week_missing_fields = [field for field in week_required_fields if field not in week_plan]

            if week_missing_fields:
                raise ValueError(f"Week {i + 1} missing required fields: {week_missing_fields}")

        # milestones 구조 검증
        if not isinstance(response["milestones"], list):
            raise ValueError("milestones must be a list")

        for i, milestone in enumerate(response["milestones"]):
            milestone_required_fields = ["week", "milestone"]
            milestone_missing_fields = [field for field in milestone_required_fields if field not in milestone]

            if milestone_missing_fields:
                raise ValueError(f"Milestone {i + 1} missing required fields: {milestone_missing_fields}")


class GeminiServiceConfig:
    """Gemini 서비스 설정"""

    # 기본 설정값
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_TOP_P = 0.8
    DEFAULT_TOP_K = 40
    DEFAULT_MAX_OUTPUT_TOKENS = 2048

    # 응답 시간 제한 (초)
    RESPONSE_TIMEOUT = 30

    # 재시도 설정
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # 초