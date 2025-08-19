import json
from google import generativeai as genai
from typing import Dict, Any, Optional
from datetime import datetime
from app.dtos.ai.study_plan import StudyPlanRequest

import logging
import json
import re

logger = logging.getLogger(__name__)


class GeminiService:
    """Gemini API 연동 서비스"""

    def __init__(self, api_key: str):
        """Gemini 서비스 초기화"""
        self.api_key = api_key
        genai.configure(api_key=api_key)

        # 응답 길이 제한 해제 및 설정 최적화
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=2048,  # 최대 토큰 수 증가
            temperature=0.3,  # 일관성 있는 응답을 위해 낮춤
            top_p=0.8,
            top_k=40
        )

        self.model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config=generation_config
        )

        # 안전 설정도 조정 (응답 차단 방지)
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]

        self.safety_settings = safety_settings

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

        # ✅ 챌린지 모드 여부에 따른 상세한 지침
        if request.is_challenge:
            challenge_instruction = f"""
    🔥 **집중 챌린지 모드** 🔥

    이것은 {duration_days}일간의 집중 챌린지입니다. 다음 사항을 반드시 포함해주세요:

    **챌린지 특화 요구사항:**
    1. **일일 목표**: 매일 달성해야 할 구체적인 목표 설정
    2. **체크포인트**: 주 단위로 명확한 성취 지표 제공
    3. **도전 과제**: 각 주마다 실력을 테스트할 수 있는 구체적인 과제
    4. **동기부여 요소**: 중간중간 성취감을 느낄 수 있는 마일스톤
    5. **집중도 극대화**: 핵심 스킬에 집중된 고강도 학습 계획
    6. **실습 중심**: 이론보다는 실제 프로젝트와 코딩에 집중
    7. **진도 체크**: 매일 또는 격일로 진도 확인이 가능한 구조

    **JSON 응답에 추가 필드 포함:**
    - "daily_goals": 각 주차별 일일 목표 배열
    - "challenge_tasks": 각 주차별 도전 과제
    - "checkpoints": 구체적인 체크포인트
    - "motivation_tips": 동기부여 팁
    """
        else:
            challenge_instruction = """
    📚 **일반 학습 모드**

    체계적이고 지속 가능한 학습 계획을 수립해주세요:
    - 점진적인 난이도 증가
    - 충분한 복습 시간 포함
    - 실무 활용 가능한 내용 구성
    """

        # ✅ 챌린지 모드에 따른 다른 JSON 스키마
        if request.is_challenge:
            json_schema = f'''
    {{
        "title": "챌린지 학습계획 제목",
        "total_weeks": {duration_weeks},
        "difficulty": "challenge|intensive|advanced",
        "challenge_mode": true,
        "weekly_plans": [
            {{
                "week": 1,
                "title": "주차별 제목",
                "topics": ["핵심 주제1", "핵심 주제2"],
                "goals": ["구체적 달성 목표1", "구체적 달성 목표2"],
                "daily_goals": [
                    "1일차: 구체적 일일 목표",
                    "2일차: 구체적 일일 목표",
                    "3일차: 구체적 일일 목표"
                ],
                "challenge_tasks": [
                    "도전 과제 1: 실제 구현해야 할 과제",
                    "도전 과제 2: 실제 구현해야 할 과제"
                ],
                "checkpoints": ["체크포인트 1", "체크포인트 2"],
                "estimated_hours": 15,
                "intensity": "high"
            }}
        ],
        "milestones": [
            {{
                "week": 2,
                "milestone": "중간 목표 및 성취 지표",
                "achievement_criteria": "구체적인 달성 기준"
            }}
        ],
        "final_challenge": "최종 프로젝트 또는 도전 과제",
        "motivation_tips": [
            "동기부여 팁 1",
            "동기부여 팁 2"
        ]
    }}'''
        else:
            json_schema = f'''
    {{
        "title": "학습계획 제목",
        "total_weeks": {duration_weeks},
        "difficulty": "beginner|intermediate|advanced|beginner_to_advanced",
        "challenge_mode": false,
        "weekly_plans": [
            {{
                "week": 1,
                "title": "주차별 제목",
                "topics": ["학습 주제1", "학습 주제2"],
                "goals": ["달성 목표1", "달성 목표2"],
                "estimated_hours": 8,
                "intensity": "moderate"
            }}
        ],
        "milestones": [
            {{
                "week": 4,
                "milestone": "중간 목표 설명"
            }}
        ]
    }}'''

        prompt = f"""
    사용자 요청: {request.input_data}

    학습 기간: {request.start_date.strftime('%Y-%m-%d')} ~ {request.end_date.strftime('%Y-%m-%d')} (총 {duration_days}일, 약 {duration_weeks}주)

    {challenge_instruction}

    다음 JSON 형식으로 상세한 학습계획을 작성해주세요:

    {json_schema}

    ⚠️ **중요 주의사항:**
    1. weekly_plans는 정확히 {duration_weeks}개의 주차 계획을 포함해야 합니다
    2. 각 주차별로 구체적이고 실행 가능한 학습 목표를 제시해주세요
    3. 난이도는 점진적으로 증가하도록 구성해주세요
    4. 실제 학습 가능한 시간을 고려해주세요
    5. {"챌린지 모드에서는 매일 실습할 수 있는 구체적인 과제를 포함해주세요" if request.is_challenge else "이론과 실습의 균형을 맞춰주세요"}
    6. JSON 형식을 정확히 지켜주세요
    7. 한국어로 작성해주세요

    응답은 반드시 올바른 JSON 형식이어야 하며, 추가 설명이나 마크다운은 포함하지 마세요.
    """

        return prompt

    async def generate_summary(
            self,
            content: str,
            summary_type: str = "general",
            title: Optional[str] = None
    ) -> Dict[str, Any]:
        """문서 요약 생성 - 줄바꿈 처리 문제 해결"""
        try:
            logger.info(f"🔍 요약 생성 시작 - 텍스트 길이: {len(content)}")
            logger.info(f"📝 텍스트 미리보기: {content[:100]}...")

            # 텍스트 길이 검증
            if not content or len(content.strip()) < 10:
                raise ValueError("요약할 텍스트가 너무 짧습니다")

            # 텍스트가 너무 길면 줄임
            if len(content) > 3000:
                logger.warning(f"텍스트가 길어서 줄입니다: {len(content)} -> 3000자")
                content = content[:3000] + "..."

            # 프롬프트 생성
            prompt = self._build_summary_prompt(content, summary_type, title)
            logger.info(f"📝 프롬프트 생성 완료")

            # Gemini API 호출
            response = await self.model.generate_content_async(
                prompt,
                safety_settings=self.safety_settings
            )

            logger.info(f"📨 Gemini 응답 길이: {len(response.text)}")
            logger.info(f"📨 Gemini 원본 응답: {response.text}")

            # 응답 정리 및 JSON 파싱
            clean_text = self._clean_gemini_response(response.text)
            logger.info(f"🧹 정리된 응답: {clean_text}")

            try:
                parsed_response = json.loads(clean_text)
                logger.info("✅ JSON 파싱 성공!")

                # 응답 검증
                self._validate_summary_response(parsed_response)
                return parsed_response

            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON 파싱 실패: {e}")
                logger.error(f"❌ 파싱 실패 텍스트: {clean_text}")
                return self._create_fallback_summary(content, summary_type, title)

        except Exception as e:
            logger.error(f"❌ 요약 생성 실패: {e}")
            return self._create_fallback_summary(content, summary_type, title)

    def _build_summary_prompt(self, content: str, summary_type: str, title: Optional[str] = None) -> str:
        """간단하고 안전한 요약 프롬프트"""

        prompt = f"""다음 텍스트를 한국어로 요약해주세요.

    텍스트: {content}

    아래 JSON 형식으로만 답변하세요:

    {{
      "summary": "핵심 내용을 2-3문장으로 요약",
      "key_points": ["요점1", "요점2", "요점3"],
      "keywords": ["키워드1", "키워드2", "키워드3"]
    }}

    중요사항:
    - 마크다운 사용 금지
    - 코드블록 사용 금지  
    - 순수 JSON만 반환
    - 모든 내용은 한국어로 작성"""

        return prompt

    def _is_response_complete(self, response: Dict[str, Any]) -> bool:
        """응답이 완전한지 검증"""
        required_fields = ["summary", "key_points", "keywords"]

        # 필수 필드 존재 확인
        for field in required_fields:
            if field not in response:
                logger.warning(f"누락된 필드: {field}")
                return False

        # summary가 너무 짧지 않은지 확인
        if len(response.get("summary", "")) < 20:
            logger.warning("요약이 너무 짧습니다")
            return False

        # key_points가 리스트인지 확인
        if not isinstance(response.get("key_points"), list):
            logger.warning("key_points가 리스트가 아닙니다")
            return False

        return True

    # gemini_service.py의 generate_study_plan 메서드에 추가

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

    def _clean_gemini_response(self, response_text: str) -> str:
        """Gemini 응답 정리"""

        logger.info(f"🔍 원본 응답 길이: {len(response_text)}")

        text = response_text.strip()

        # 마크다운 코드 블록 제거
        if text.startswith("```json") and text.endswith("```"):
            text = text[7:-3].strip()
            logger.info("✅ ```json``` 블록 제거")
        elif text.startswith("```") and text.endswith("```"):
            text = text[3:-3].strip()
            logger.info("✅ ``` 블록 제거")

        # 중간에 있는 마크다운 블록도 처리
        import re
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'\s*```', '', text)

        # 줄바꿈을 공백으로 변경 (JSON 구조 보존)
        text = re.sub(r'\n+', ' ', text)

        # 연속된 공백 정리
        text = re.sub(r'\s+', ' ', text)

        # 앞뒤 공백 제거
        text = text.strip()

        logger.info(f"🧹 정리 후 길이: {len(text)}")

        return text

    def _validate_summary_response(self, response: Dict[str, Any]) -> None:
        """요약 응답 검증"""
        required_fields = ["summary"]

        # 필수 필드 확인
        missing_fields = [field for field in required_fields if field not in response]
        if missing_fields:
            raise ValueError(f"요약 응답에서 필수 필드 누락: {missing_fields}")

        # summary 필드가 비어있지 않은지 확인
        if not response["summary"] or not response["summary"].strip():
            raise ValueError("요약 내용이 비어있습니다")

    def _create_fallback_summary(self, content: str, summary_type: str, title: Optional[str] = None) -> Dict[str, Any]:
        """폴백 요약 생성 - 범용적 버전"""

        # 간단한 문장 분리
        sentences = content.replace('!', '.').replace('?', '.').split('.')
        clean_sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

        # 첫 2문장으로 요약 생성
        summary_sentences = clean_sentences[:2] if len(clean_sentences) >= 2 else clean_sentences[:1]
        fallback_summary = '. '.join(summary_sentences)

        if not fallback_summary:
            fallback_summary = content[:100].strip()
            if len(content) > 100:
                fallback_summary += "..."

        # 간단한 키워드 추출
        import re
        words = re.findall(r'[가-힣a-zA-Z0-9]+', content)
        word_freq = {}
        for word in words:
            if len(word) >= 2 and not word.isdigit():
                word_freq[word] = word_freq.get(word, 0) + 1

        # 빈도순 상위 키워드
        if word_freq:
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            keywords = [word for word, freq in sorted_words[:5]]
        else:
            keywords = ["문서", "내용", "정보"]

        return {
            "summary": fallback_summary,
            "key_points": [
                "주요 내용 요약",
                "핵심 정보 설명",
                "중요 사항 정리"
            ],
            "keywords": keywords[:3],
            "_fallback": True,
            "_reason": "Gemini 응답 처리 실패"
        }

    def _validate_and_fix_response(self, response: Dict[str, Any], original_content: str) -> Dict[str, Any]:
        """응답 구조 검증 및 수정"""

        # 필수 필드 확인 및 보완
        if "summary" not in response or not response["summary"]:
            # 원본 텍스트에서 첫 문장들로 요약 생성
            sentences = original_content.split('.')[:2]
            response["summary"] = '. '.join(s.strip() for s in sentences if s.strip()) + '.'

        if "key_points" not in response or not isinstance(response["key_points"], list):
            response["key_points"] = ["주요 내용 추출 실패"]

        if "keywords" not in response or not isinstance(response["keywords"], list):
            # 간단한 키워드 추출
            words = original_content.split()
            common_words = ['AWS', '기술', '서비스', '데이터', '머신러닝']
            response["keywords"] = [w for w in common_words if w in original_content][:5]

        if "word_count" not in response:
            response["word_count"] = len(original_content.split())

        if "summary_ratio" not in response:
            summary_len = len(response["summary"].split())
            original_len = len(original_content.split())
            ratio = round((summary_len / original_len) * 100) if original_len > 0 else 0
            response["summary_ratio"] = f"{ratio}%"

        return response


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