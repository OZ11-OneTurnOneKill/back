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

    def _extract_text_from_response(self, response) -> str:
        """Gemini 응답에서 텍스트 추출 (강화된 디버깅 버전)

        Args:
            response: Gemini API 응답 객체

        Returns:
            추출된 텍스트

        Raises:
            ValueError: 텍스트 추출 실패 시
        """
        logger.info(f"🔍 응답 객체 타입: {type(response)}")
        logger.info(f"🔍 응답 객체 속성: {dir(response)}")

        # 응답 객체 전체 구조 로깅
        try:
            logger.info(f"🔍 응답 객체 전체 정보: {str(response)}")
        except:
            logger.info("🔍 응답 객체 str() 변환 실패")

        try:
            # 방법 1: response.text가 가능한 경우 (단순 응답)
            logger.info("🔍 방법 1: response.text 시도")
            if hasattr(response, 'text'):
                logger.info(f"🔍 response.text 존재: {response.text is not None}")
                if response.text:
                    logger.info(f"✅ 방법 1 성공: {len(response.text)} 문자")
                    return response.text
                else:
                    logger.warning("⚠️ response.text가 None 또는 빈 문자열")
            else:
                logger.warning("⚠️ response.text 속성이 존재하지 않음")
        except Exception as e:
            logger.warning(f"⚠️ response.text 접근 실패: {e}")

        try:
            # 방법 2: response.parts 사용
            logger.info("🔍 방법 2: response.parts 시도")
            if hasattr(response, 'parts'):
                logger.info(f"🔍 response.parts 존재: {response.parts is not None}")
                if response.parts:
                    text_parts = []
                    for i, part in enumerate(response.parts):
                        logger.info(f"🔍 Part {i}: {type(part)}, hasattr text: {hasattr(part, 'text')}")
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                    if text_parts:
                        result = ''.join(text_parts)
                        logger.info(f"✅ 방법 2 성공: {len(result)} 문자")
                        return result
                else:
                    logger.warning("⚠️ response.parts가 None 또는 빈 리스트")
            else:
                logger.warning("⚠️ response.parts 속성이 존재하지 않음")
        except Exception as e:
            logger.warning(f"⚠️ response.parts 접근 실패: {e}")

        try:
            # 방법 3: candidates를 통한 접근
            logger.info("🔍 방법 3: candidates 시도")
            if hasattr(response, 'candidates'):
                logger.info(f"🔍 candidates 존재: {response.candidates is not None}")
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    logger.info(f"🔍 첫 번째 candidate: {type(candidate)}")

                    if hasattr(candidate, 'content'):
                        content = candidate.content
                        logger.info(f"🔍 candidate.content: {type(content)}")

                        if hasattr(content, 'parts'):
                            logger.info(f"🔍 content.parts 존재: {content.parts is not None}")
                            if content.parts:
                                text_parts = []
                                for i, part in enumerate(content.parts):
                                    logger.info(f"🔍 Content Part {i}: {type(part)}")
                                    if hasattr(part, 'text') and part.text:
                                        text_parts.append(part.text)
                                if text_parts:
                                    result = ''.join(text_parts)
                                    logger.info(f"✅ 방법 3 성공: {len(result)} 문자")
                                    return result
                else:
                    logger.warning("⚠️ candidates가 None 또는 빈 리스트")
            else:
                logger.warning("⚠️ candidates 속성이 존재하지 않음")
        except Exception as e:
            logger.warning(f"⚠️ candidates 접근 실패: {e}")

        # 방법 4: _result 속성 확인 (일부 경우)
        try:
            logger.info("🔍 방법 4: _result 시도")
            if hasattr(response, '_result'):
                logger.info(f"🔍 _result 존재: {response._result}")
                # _result에서 텍스트 추출 시도
        except Exception as e:
            logger.warning(f"⚠️ _result 접근 실패: {e}")

        # 모든 방법 실패 시 - 더 상세한 디버깅 정보
        logger.error(f"❌ 모든 텍스트 추출 방법 실패")
        logger.error(f"❌ Response 구조: {type(response)}")

        try:
            if hasattr(response, '__dict__'):
                logger.error(f"❌ Response __dict__: {response.__dict__}")
        except:
            logger.error("❌ Response __dict__ 접근 실패")

        # 임시로 빈 JSON 반환하여 완전 실패 방지
        logger.warning("⚠️ 임시 빈 응답 반환")
        return '{"title": "임시 학습계획", "total_weeks": 4, "weekly_plans": []}'

    async def generate_study_plan(self, request) -> Dict[str, Any]:
        """디버깅이 추가된 학습계획 생성"""
        try:
            logger.info(f"🔍 API 키 확인: {self.api_key[:10]}..." if self.api_key else "❌ API 키 없음")

            prompt = self._build_prompt(request)
            logger.info(f"📝 프롬프트 생성 완료: {len(prompt)} 문자")

            # Gemini API 호출
            response = await self.model.generate_content_async(prompt)
            logger.info(f"📨 Gemini 응답 받음")

            # 🔥 수정된 부분: 안전한 텍스트 추출
            response_text = self._extract_text_from_response(response)
            logger.info(f"📄 응답 텍스트 추출 성공: {len(response_text)} 문자")
            logger.info(f"📄 실제 응답 내용: {response_text[:500]}...")

            # JSON 파싱 시도 (개선된 로직)
            try:
                clean_text = response_text.strip()
                logger.info(f"🧹 원본 텍스트 길이: {len(clean_text)}")
                logger.info(f"🧹 원본 텍스트 시작: {clean_text[:100]}...")
                logger.info(f"🧹 원본 텍스트 끝: {clean_text[-100:]}")

                # 더 안전한 코드 블록 제거
                if clean_text.startswith("```json"):
                    # ```json으로 시작하는 경우
                    start_index = clean_text.find('\n') + 1  # 첫 번째 줄바꿈 다음부터
                    end_index = clean_text.rfind("```")  # 마지막 ``` 위치
                    if end_index > start_index:
                        clean_text = clean_text[start_index:end_index]
                    else:
                        clean_text = clean_text[7:]  # ```json 제거만
                elif clean_text.startswith("```"):
                    # ```로 시작하는 경우
                    start_index = clean_text.find('\n') + 1
                    end_index = clean_text.rfind("```")
                    if end_index > start_index:
                        clean_text = clean_text[start_index:end_index]
                    else:
                        clean_text = clean_text[3:]  # ``` 제거만

                clean_text = clean_text.strip()
                logger.info(f"🧹 정리된 텍스트 길이: {len(clean_text)}")
                logger.info(f"🧹 정리된 텍스트 시작: {clean_text[:200]}...")

                parsed_response = json.loads(clean_text)
                logger.info("✅ JSON 파싱 성공!")

                return parsed_response

            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON 파싱 실패: {e}")
                logger.error(f"❌ 파싱 실패 원본: {response_text}")

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
                    "_fallback": True,
                    "_raw_response": response_text  # 디버깅용
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
    7. **진척 추적**: 매일 체크할 수 있는 구체적인 성과 지표
    """
        else:
            challenge_instruction = f"""
    📚 **일반 학습 모드** 📚

    이것은 {duration_days}일간의 체계적인 학습 계획입니다.
    사용자의 페이스에 맞춰 꾸준히 학습할 수 있도록 구성해주세요.
    """

        prompt = f"""
당신은 전문 교육 컨설턴트입니다. 사용자의 요청에 맞춰 최적의 학습 계획을 작성해주세요.

{challenge_instruction}

**요청 정보:**
- 학습 주제: {request.input_data}
- 시작일: {request.start_date.strftime('%Y-%m-%d')}
- 종료일: {request.end_date.strftime('%Y-%m-%d')}
- 총 기간: {duration_days}일 ({duration_weeks}주)
- 챌린지 모드: {'예' if request.is_challenge else '아니오'}

**응답 형식 (반드시 JSON으로만 응답):**
```json
{{
    "title": "학습계획 제목",
    "total_weeks": {duration_weeks},
    "difficulty": "beginner|intermediate|advanced",
    "estimated_total_hours": 0,
    "weekly_plans": [
        {{
            "week": 1,
            "title": "1주차 제목",
            "topics": ["주제1", "주제2", "주제3"],
            "goals": ["목표1", "목표2"],
            "estimated_hours": 0,
            "difficulty_level": "beginner|intermediate|advanced"
        }}
    ],
    "milestones": [
        {{
            "week": 2,
            "milestone": "달성할 마일스톤",
            "verification_method": "검증 방법"
        }}
    ],
    "resources": [
        {{
            "type": "documentation|tutorial|video|book",
            "title": "자료 제목",
            "url": "https://example.com",
            "priority": "high|medium|low"
        }}
    ]
}}
```

**중요한 지침:**
1. 응답은 반드시 유효한 JSON 형식이어야 합니다
2. 주석이나 설명 텍스트 없이 순수 JSON만 반환하세요
3. 실무에 바로 적용 가능한 구체적인 내용으로 구성하세요
4. 각 주차별로 명확한 학습 목표와 검증 방법을 제시하세요
5. 학습자의 수준을 고려하여 단계적으로 난이도를 조절하세요

지금 바로 위 형식에 맞춰 학습계획을 JSON으로 생성해주세요.
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