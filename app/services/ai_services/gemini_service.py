import json
from google import generativeai as genai
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.dtos.ai.study_plan import StudyPlanRequest

import logging
import json
import re

logger = logging.getLogger(__name__)


class GeminiService:
    """Gemini API 연동 서비스 - 완전 범용 학습계획 생성기"""

    def __init__(self, api_key: str):
        """Gemini 서비스 초기화"""
        self.api_key = api_key
        genai.configure(api_key=api_key)

        generation_config = genai.types.GenerationConfig(
            max_output_tokens=2048,
            temperature=0.3,
            top_p=0.8,
            top_k=40
        )

        self.model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config=generation_config
        )

        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
        self.safety_settings = safety_settings

    def _extract_text_from_response(self, response) -> str:
        """Gemini 응답에서 텍스트 추출"""
        try:
            if hasattr(response, 'text') and response.text:
                return response.text
        except Exception as e:
            logger.warning(f"⚠️ response.text 접근 실패: {e}")

        try:
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        if text_parts:
                            return ''.join(text_parts)
        except Exception as e:
            logger.warning(f"⚠️ candidates 접근 실패: {e}")

        logger.error("❌ 모든 텍스트 추출 방법 실패")
        return "빈 응답"

    async def generate_study_plan(self, request) -> Dict[str, Any]:
        """완전 범용 학습계획 생성 시스템"""
        try:
            logger.info(f"🔍 API 키 확인: {self.api_key[:10]}..." if self.api_key else "❌ API 키 없음")

            prompt = self._build_universal_prompt(request)
            logger.info(f"📝 프롬프트 생성 완료: {len(prompt)} 문자")

            # Gemini API 호출
            response = await self.model.generate_content_async(prompt)
            response_text = self._extract_text_from_response(response)
            logger.info(f"📄 응답 텍스트 추출 성공: {len(response_text)} 문자")

            # JSON 파싱 시도
            try:
                clean_text = self._clean_json_response(response_text)
                parsed_response = json.loads(clean_text)
                logger.info("✅ JSON 파싱 성공!")
                return parsed_response

            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON 파싱 실패: {e}")
                return self._generate_intelligent_fallback_plan(request, response_text)

        except Exception as e:
            logger.error(f"❌ Gemini API 호출 전체 실패: {e}")
            return self._generate_intelligent_fallback_plan(request, str(e))

    def _clean_json_response(self, response_text: str) -> str:
        """JSON 응답 정리"""
        clean_text = response_text.strip()

        if clean_text.startswith("```json"):
            start_index = clean_text.find('\n') + 1
            end_index = clean_text.rfind("```")
            if end_index > start_index:
                clean_text = clean_text[start_index:end_index]
            else:
                clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            start_index = clean_text.find('\n') + 1
            end_index = clean_text.rfind("```")
            if end_index > start_index:
                clean_text = clean_text[start_index:end_index]
            else:
                clean_text = clean_text[3:]

        return clean_text.strip()

    def _build_universal_prompt(self, request: StudyPlanRequest) -> str:
        """완전 범용 프롬프트 생성기 - 어떤 분야든 대응"""

        duration_days = (request.end_date - request.start_date).days
        duration_weeks = max(1, duration_days // 7)

        # 사용자 입력 분석
        subject_analysis = self._analyze_user_input(request.input_data)
        duration_info = self._get_duration_characteristics(duration_weeks)
        challenge_instruction = self._get_challenge_instruction(request.is_challenge, duration_weeks)

        prompt = f"""
당신은 세계 최고의 교육 설계 전문가이자 학습 컨설턴트입니다.
사용자가 요청한 "{request.input_data}"에 대한 {duration_weeks}주간 학습계획을 설계해주세요.

{challenge_instruction}

**사용자 요청 분석:**
- 학습 주제: {request.input_data}
- 학습 기간: {duration_days}일 ({duration_weeks}주)
- 목표 키워드: {subject_analysis['keywords']}
- 학습 목적: {subject_analysis['purpose']}
- 예상 난이도: {duration_info['difficulty']}
- 권장 학습시간: {duration_info['recommended_hours']}시간

**설계 철학:**
1. **적응성**: 어떤 분야든 체계적으로 접근
2. **실용성**: 실제 생활이나 업무에 바로 적용 가능
3. **진행성**: 기초 → 중급 → 고급 → 마스터 단계적 발전
4. **구체성**: 추상적 표현 금지, 명확하고 구체적인 내용
5. **검증성**: 학습 성과를 측정할 수 있는 명확한 기준

**학습 단계 설계 원칙:**
- 1단계 (기초): 개념 이해 + 기본 도구/방법 습득
- 2단계 (응용): 실무 기법 + 실습 프로젝트 수행  
- 3단계 (심화): 고급 기법 + 창의적 응용
- 4단계 (완성): 전문성 구축 + 실전 적용

**필수 포함 요소:**
- {duration_weeks}주 전체 상세 계획
- 매주 7일간 구체적 일별 목표
- 실습할 수 있는 구체적 과제
- 학습 성과 측정 방법
- 추천 학습 자료와 도구
- 실전 활용 팁

**JSON 응답 형식:**
```json
{{
    "title": "{duration_weeks}주 완전 마스터 과정",
    "total_weeks": {duration_weeks},
    "difficulty": "{duration_info['difficulty']}",
    "estimated_total_hours": {duration_info['recommended_hours']},
    "description": "이 과정을 통해 달성할 수 있는 최종 목표와 핵심 가치",
    "weekly_plans": [
        {{
            "week": 1,
            "title": "1주차: 기초 완성",
            "theme": "Foundation Building",
            "topics": ["기본 개념", "도구 사용법", "기초 실습"],
            "daily_goals": [
                "1일: 개요 파악 및 환경 구성",
                "2일: 핵심 개념 이해",
                "3일: 기초 도구 사용법",
                "4일: 간단한 실습",
                "5일: 기초 이론 적용",
                "6일: 미니 프로젝트",
                "7일: 복습 및 정리"
            ],
            "goals": ["기본 개념 이해", "기초 실습 완료"],
            "assignments": ["기초 과제", "실습 프로젝트"],
            "estimated_hours": {int(duration_info['recommended_hours'] / duration_weeks)},
            "difficulty_level": "beginner"
        }}
    ],
    "milestones": [
        {{
            "week": {max(1, duration_weeks // 4)},
            "milestone": "기초 완성",
            "verification_method": "기본 테스트 통과"
        }}
    ],
    "resources": [
        {{
            "type": "essential",
            "title": "기초 학습 자료",
            "url": "관련 사이트 또는 교재",
            "priority": "high"
        }}
    ],
    "tips": [
        "매일 꾸준한 학습",
        "이론과 실습의 균형",
        "어려운 부분 반복 학습"
    ]
}}
```

**중요 지침:**
- 반드시 완벽한 JSON 형식으로만 응답
- {duration_weeks}주 전체 계획을 상세히 작성
- 각 주마다 7일간의 구체적인 daily_goals 제공
- 실현 가능하고 측정 가능한 목표 설정

지금 바로 "{request.input_data}" 분야의 최고 품질 {duration_weeks}주 학습계획을 JSON으로 생성해주세요.
"""
        return prompt

    def _analyze_user_input(self, input_text: str) -> Dict[str, Any]:
        """사용자 입력 지능적 분석 - 어떤 분야든 분석"""

        # 🔥 핵심 주제 추출 (길이 제한)
        core_subject = self._extract_core_subject(input_text)

        # 기본 정보 추출
        words = input_text.lower().split()

        # 키워드 추출 (조사, 전치사 등 제거)
        stop_words = ['을', '를', '이', '가', '에', '에서', '으로', '로', '와', '과', '의', '은', '는',
                      '하고', '하는', '하기', '에대해', '에 대해', '공부', '학습', '배우', '익히',
                      '나는', '내가', '저는', '제가', '하루에', '시간씩', '투자', '가능하고', '포함해줘',
                      '주고', '만들어줘', '추가해주고', '하고싶어', '싶어', '원해', '바래']
        keywords = [word for word in words if word not in stop_words and len(word) > 1]

        # 학습 목적 추론
        purpose = self._infer_learning_purpose(input_text)

        # 분야 유형 추론
        field_type = self._infer_field_type(input_text, keywords)

        # 학습 접근법 추론
        approach = self._infer_learning_approach(field_type)

        # 핵심 스킬 추론
        skills = self._infer_key_skills(keywords, field_type)

        # 실용적 활용법 추론
        applications = self._infer_practical_applications(keywords, field_type)

        return {
            "core_subject": core_subject,  # 🔥 추가: 핵심 주제
            "keywords": keywords[:5],  # 상위 5개 키워드
            "purpose": purpose,
            "field_type": field_type,
            "approach": approach,
            "skills": skills,
            "applications": applications
        }

    def _extract_core_subject(self, input_text: str) -> str:
        """사용자 입력에서 핵심 주제만 추출 (완전 범용)"""

        # 불필요한 문구들 제거
        noise_phrases = [
            '나는', '저는', '내가', '제가', '우리는', '우리가',
            '하고 싶어', '하고싶어', '원해', '바래', '하려고',
            '공부하고', '배우고', '익히고', '학습하고', '마스터하고',
            '집중적으로', '체계적으로', '꼼꼼히', '완전히',
            '기간 동안', '시간 동안', '시간씩', '투자 가능하고',
            '포함해줘', '주고', '만들어줘', '추가해주고', '하고 싶어'
        ]

        # 입력 텍스트 정리
        cleaned_text = input_text
        for phrase in noise_phrases:
            cleaned_text = cleaned_text.replace(phrase, ' ')

        # 연속 공백 제거
        cleaned_text = ' '.join(cleaned_text.split())

        # 핵심 키워드 추출 (첫 번째 문장에서)
        sentences = cleaned_text.split('.')
        if sentences:
            first_sentence = sentences[0].strip()

            # 조사, 전치사 등 제거
            words = first_sentence.split()
            meaningful_words = []

            for word in words:
                # 의미 있는 단어만 선택 (2글자 이상, 숫자나 특수문자 포함 X)
                if (len(word) >= 2 and
                        not word.isdigit() and
                        word not in ['동안', '까지', '부터', '에서', '으로', '에게']):
                    meaningful_words.append(word)

            # 처음 1-2개 의미 있는 단어로 주제 구성
            if meaningful_words:
                if len(meaningful_words) == 1:
                    return meaningful_words[0]
                elif len(meaningful_words) >= 2:
                    # 두 단어 조합으로 의미 있는 주제 만들기
                    return ' '.join(meaningful_words[:2])

        # 추출 실패 시 기본값
        return "맞춤형 학습"

    def _infer_learning_purpose(self, input_text: str) -> str:
        """학습 목적 추론"""
        input_lower = input_text.lower()

        if any(word in input_lower for word in ['취업', '면접', '이직', '커리어']):
            return "취업/커리어 준비"
        elif any(word in input_lower for word in ['시험', '자격증', '인증', '점수']):
            return "시험/자격증 취득"
        elif any(word in input_lower for word in ['취미', '여가', '즐거움', '재미']):
            return "취미/개인 발전"
        elif any(word in input_lower for word in ['업무', '직무', '실무', '회사']):
            return "업무 역량 강화"
        elif any(word in input_lower for word in ['창업', '사업', '비즈니스']):
            return "창업/사업 준비"
        else:
            return "전문성 개발 및 역량 강화"

    def _infer_field_type(self, input_text: str, keywords: List[str]) -> str:
        """분야 유형 범용 추론"""
        input_lower = input_text.lower()

        # 학습 방식에 따른 분류 (구체적 기술보다는 학습 특성으로 분류)
        if any(word in input_lower for word in ['프로그래밍', '개발', '코딩', '컴퓨터', '소프트웨어', 'it']):
            return "기술/개발"
        elif any(word in input_lower for word in ['언어', '회화', '번역', '통역', '외국어']):
            return "언어/소통"
        elif any(word in input_lower for word in ['창작', '예술', '디자인', '작품', '표현']):
            return "창작/예술"
        elif any(word in input_lower for word in ['사업', '경영', '마케팅', '경제', '금융', '회계']):
            return "비즈니스/경영"
        elif any(word in input_lower for word in ['운동', '건강', '생활', '요리', '취미']):
            return "생활/실용"
        elif any(word in input_lower for word in ['학문', '연구', '이론', '과학', '수학', '학습']):
            return "학문/연구"
        elif any(word in input_lower for word in ['자격증', '시험', '인증', '합격']):
            return "자격/시험"
        else:
            return "일반/기타"

    def _infer_learning_approach(self, field_type: str) -> str:
        """학습 접근법 범용 추론"""
        approach_map = {
            "기술/개발": "이론 학습 + 실습 중심 + 프로젝트 완성",
            "언어/소통": "듣기, 말하기, 읽기, 쓰기 4영역 균형 학습",
            "창작/예술": "기초 이론 + 창작 실습 + 작품 완성",
            "비즈니스/경영": "이론 학습 + 사례 분석 + 실무 적용",
            "학문/연구": "개념 이해 + 논리적 사고 + 문제 해결",
            "생활/실용": "기초 이론 + 실전 연습 + 응용 활용",
            "자격/시험": "이론 정리 + 문제 풀이 + 실전 시험",
            "일반/기타": "체계적 이론 학습 + 단계적 실무 적용"
        }
        return approach_map.get(field_type, "체계적 이론 학습 + 실무 적용")

    def _infer_key_skills(self, keywords: List[str], field_type: str) -> List[str]:
        """핵심 스킬 범용 추론"""
        base_skills = {
            "기술/개발": ["논리적 사고", "문제 해결", "도구 활용", "프로젝트 완성"],
            "언어/소통": ["의사소통", "표현 능력", "이해력", "문화적 소양"],
            "창작/예술": ["창의적 표현", "미적 감각", "기술적 숙련", "작품 완성"],
            "비즈니스/경영": ["분석적 사고", "전략 기획", "의사결정", "실행력"],
            "학문/연구": ["이론적 이해", "논리적 사고", "연구 방법", "비판적 분석"],
            "생활/실용": ["기본 기법", "응용 능력", "실생활 적용", "지속적 실천"],
            "자격/시험": ["이론 정리", "문제 해결", "시간 관리", "실전 대응"],
            "일반/기타": ["기초 이해", "체계적 사고", "실무 적용", "지속적 학습"]
        }

        # 키워드 기반 맞춤 스킬 추가
        if keywords:
            custom_skills = [f"{keywords[0]} 전문 역량"]
        else:
            custom_skills = ["전문 지식 습득"]

        return base_skills.get(field_type, ["기초 이해", "실무 적용", "전문성 개발"]) + custom_skills

    def _infer_practical_applications(self, keywords: List[str], field_type: str) -> List[str]:
        """실용적 활용법 범용 추론"""
        base_applications = {
            "기술/개발": ["업무 효율화", "개인 프로젝트", "포트폴리오 구축", "커리어 발전"],
            "언어/소통": ["소통 능력 향상", "글로벌 활동", "문화 교류", "자기계발"],
            "창작/예술": ["작품 활동", "개인 표현", "취미 생활", "부가 수입"],
            "비즈니스/경영": ["업무 역량", "의사결정", "경영 능력", "사업 기회"],
            "학문/연구": ["지식 확장", "연구 활동", "교육 능력", "전문성 인정"],
            "생활/실용": ["일상 개선", "건강 관리", "취미 생활", "삶의 질 향상"],
            "자격/시험": ["자격 취득", "취업 준비", "승진 기회", "전문성 인증"],
            "일반/기타": ["개인 발전", "실무 활용", "전문성 구축", "네트워킹"]
        }

        return base_applications.get(field_type, ["개인 발전", "실무 활용", "전문성 구축"])

    def _get_duration_characteristics(self, weeks: int) -> Dict[str, Any]:
        """기간별 특성 분석"""
        if weeks <= 1:
            return {
                "characteristics": "속성 입문",
                "difficulty": "beginner",
                "recommended_hours": 8,
                "intensity": "매우 높음"
            }
        elif weeks <= 4:
            return {
                "characteristics": "집중 기초",
                "difficulty": "beginner_to_intermediate",
                "recommended_hours": weeks * 12,
                "intensity": "높음"
            }
        elif weeks <= 8:
            return {
                "characteristics": "체계적 학습",
                "difficulty": "intermediate",
                "recommended_hours": weeks * 10,
                "intensity": "보통"
            }
        elif weeks <= 16:
            return {
                "characteristics": "심화 학습",
                "difficulty": "intermediate_to_advanced",
                "recommended_hours": weeks * 8,
                "intensity": "보통"
            }
        else:
            return {
                "characteristics": "전문가 과정",
                "difficulty": "advanced",
                "recommended_hours": weeks * 6,
                "intensity": "낮음"
            }

    def _get_challenge_instruction(self, is_challenge: bool, weeks: int) -> str:
        """챌린지 모드별 지침"""
        if is_challenge:
            return f"""
🔥 **{weeks}주 집중 챌린지 모드** 🔥
- 고강도 몰입 학습으로 최대 효과 달성
- 매일 구체적이고 도전적인 목표 설정
- 실습과 프로젝트 중심의 체험 학습
- 주차별 명확한 성취 기준과 인증 방법
- 포기하지 않는 강한 의지력과 지속성 요구
"""
        else:
            return f"""
📚 **{weeks}주 체계적 학습 모드** 📚
- 개인 페이스에 맞춘 지속 가능한 학습
- 이론과 실습의 균형잡힌 커리큘럼
- 단계적 난이도 상승과 충분한 복습
- 안정적 기초 구축과 점진적 발전
- 장기적 관점의 견고한 실력 완성
"""

    def _generate_intelligent_fallback_plan(self, request, error_info: str) -> Dict[str, Any]:
        """지능형 대체 학습계획 생성"""

        if request:
            input_text = request.input_data
            duration_days = (request.end_date - request.start_date).days
            duration_weeks = max(1, duration_days // 7)
            is_challenge = getattr(request, 'is_challenge', False)
        else:
            input_text = "일반 학습"
            duration_weeks = 4
            is_challenge = False

        # 사용자 입력 분석
        analysis = self._analyze_user_input(input_text)
        duration_info = self._get_duration_characteristics(duration_weeks)

        # 완전한 학습계획 동적 생성
        return self._create_adaptive_study_plan(
            input_text, analysis, duration_weeks, duration_info, is_challenge, error_info
        )

    def _create_adaptive_study_plan(
            self,
            subject: str,
            analysis: Dict[str, Any],
            weeks: int,
            duration_info: Dict[str, Any],
            is_challenge: bool,
            error_info: str
    ) -> Dict[str, Any]:
        """완전 적응형 학습계획 생성"""

        mode = "집중 챌린지" if is_challenge else "체계적 학습"

        # 🔥 핵심 주제 사용 (길이 제한된 깔끔한 제목)
        core_subject = analysis.get('core_subject', 'Python')  # 기본값은 Python

        # 기본 계획 구조
        plan = {
            "title": f"{weeks}주 {core_subject} 완전 마스터 {mode} 과정",
            "total_weeks": weeks,
            "difficulty": duration_info['difficulty'],
            "estimated_total_hours": duration_info['recommended_hours'],
            "description": f"{core_subject} 분야의 {duration_info['characteristics']} 학습을 통해 {analysis['purpose']} 달성",
            "subject_analysis": {
                "field_type": analysis['field_type'],
                "learning_approach": analysis['approach'],
                "key_skills": analysis['skills'],
                "practical_applications": analysis['applications']
            },
            "weekly_plans": [],
            "milestones": [],
            "resources": [],
            "tips": [
                "매일 꾸준한 학습이 성공의 핵심",
                "이론과 실습의 균형을 맞추어 진행",
                "실패를 학습의 기회로 받아들이기",
                "동료나 전문가와 적극적으로 소통하기"
            ],
            "success_factors": [
                "일관된 학습 습관과 효율적 시간 관리",
                "능동적인 실습과 지속적인 도전 정신",
                "피드백 수용과 지속적인 개선 의지",
                "실무 적용을 위한 창의적 사고력"
            ],
            "_fallback": True,
            "_source": "intelligent_adaptive_plan",
            "_core_subject": core_subject,  # 🔥 추가: 디버깅용
            "_original_input": subject[:50] + "..." if len(subject) > 50 else subject,  # 🔥 추가: 원본 확인용
            "_analysis": analysis,
            "_error_info": error_info[:100] if error_info else "none"
        }

        # 주차별 계획 동적 생성 (핵심 주제 사용)
        for week in range(1, weeks + 1):
            week_plan = self._generate_adaptive_week_plan(week, weeks, core_subject, analysis, duration_info)
            plan["weekly_plans"].append(week_plan)

        # 마일스톤 동적 생성 (핵심 주제 사용)
        plan["milestones"] = self._generate_adaptive_milestones(weeks, core_subject, analysis)

        # 자료 동적 생성 (핵심 주제 사용)
        plan["resources"] = self._generate_adaptive_resources(core_subject, analysis)

        return plan

    def _generate_adaptive_week_plan(
            self,
            week: int,
            total_weeks: int,
            subject: str,
            analysis: Dict[str, Any],
            duration_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """적응형 주차별 계획 생성"""

        # 진행률 기반 단계 결정
        progress = week / total_weeks

        if progress <= 0.25:
            stage = "기초"
            stage_en = "Foundation"
            difficulty = "beginner"
            focus = "개념 이해와 기본기 다지기"
        elif progress <= 0.5:
            stage = "응용"
            stage_en = "Application"
            difficulty = "intermediate"
            focus = "실무 기법과 응용 능력"
        elif progress <= 0.75:
            stage = "심화"
            stage_en = "Advanced"
            difficulty = "intermediate"
            focus = "고급 기법과 전문성"
        else:
            stage = "완성"
            stage_en = "Mastery"
            difficulty = "advanced"
            focus = "통합과 실전 적용"

        # 분야별 맞춤 주제 생성
        topics = self._generate_stage_topics(stage, subject, analysis)

        # 일별 목표 동적 생성
        daily_goals = self._generate_daily_goals(week, stage, subject)

        # 목표 및 과제 생성 (완전 범용)
        goals = [
            f"{subject} {stage} 단계 핵심 개념 완전 이해",
            f"{focus}을 통한 실무 역량 개발",
            f"다음 단계 진행을 위한 견고한 기반 구축"
        ]

        # 완전 범용 과제 생성
        assignments = [
            f"{stage} 수준의 {subject} 실습 과제 완성",
            f"{subject} 관련 미니 프로젝트 수행",
            f"{week}주차 학습 성과 정리 및 발표 준비"
        ]

        return {
            "week": week,
            "title": f"{week}주차: {subject} {stage} 마스터",
            "theme": f"{stage_en} & {focus}",
            "topics": topics,
            "daily_goals": daily_goals,
            "goals": goals,
            "assignments": assignments,
            "estimated_hours": duration_info['recommended_hours'] // total_weeks,
            "difficulty_level": difficulty
        }

    def _generate_stage_topics(self, stage: str, subject: str, analysis: Dict[str, Any]) -> List[str]:
        """단계별 주제 완전 범용 생성"""

        keywords = analysis.get('keywords', [])
        main_keyword = keywords[0] if keywords else subject

        if stage == "기초":
            return [
                f"{subject}의 핵심 개념과 기본 용어 정리",
                f"학습에 필요한 도구와 환경 구성",
                f"{main_keyword} 기초 이론과 기본 원리",
                f"기본 기법과 방법론 이해",
                f"간단한 실습을 통한 기초 적용",
                f"학습 방향 설정과 기초 다지기"
            ]
        elif stage == "응용":
            return [
                f"{subject} 중급 개념과 실무 활용법",
                f"효율적인 작업 방법과 도구 숙련",
                f"실전 기법과 응용 방법론",
                f"문제 해결 접근법과 전략",
                f"품질 향상을 위한 개선 기법",
                f"실무 사례 분석과 적용 연습"
            ]
        elif stage == "심화":
            return [
                f"{subject} 고급 기법과 전문 지식",
                f"창의적 접근법과 혁신적 방법",
                f"다양한 분야와의 연계 활용",
                f"최신 동향과 발전 방향",
                f"전문가 수준의 결과물 창출",
                f"네트워킹과 지식 공유 활동"
            ]
        else:  # 완성
            return [
                f"{subject} 전문성의 통합과 완성",
                f"실전 적용과 성과 측정 방법",
                f"지속적 발전을 위한 체계 구축",
                f"지식 전달과 멘토링 능력",
                f"실무 활용과 가치 창출 방안",
                f"평생 학습과 지속적 성장"
            ]

    def _generate_daily_goals(self, week: int, stage: str, subject: str) -> List[str]:
        """일별 목표 완전 범용 생성"""

        return [
            f"1일: {subject} {stage} 단계의 핵심 개념 학습",
            f"2일: 기본 도구와 방법론 실습 연습",
            f"3일: 학습 내용의 실전 적용 시도",
            f"4일: 응용 과제 또는 프로젝트 수행",
            f"5일: 복습과 심화를 통한 완전 이해",
            f"6일: 창의적 활용과 확장 학습",
            f"7일: {week}주차 성과 정리 및 다음 준비"
        ]

    def _generate_adaptive_milestones(self, weeks: int, subject: str, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """적응형 마일스톤 생성"""

        milestones = []

        # 기간에 따른 마일스톤 설정
        if weeks <= 4:
            milestone_weeks = [weeks]
            milestone_names = [f"{subject} 기초 완성"]
        elif weeks <= 8:
            milestone_weeks = [weeks // 2, weeks]
            milestone_names = [f"{subject} 기초 완성", f"{subject} 실무 활용"]
        else:
            milestone_weeks = [weeks // 4, weeks // 2, (weeks * 3) // 4, weeks]
            milestone_names = [
                f"{subject} 기초 완성",
                f"{subject} 응용 능력",
                f"{subject} 심화 전문성",
                f"{subject} 마스터 달성"
            ]

        for week, name in zip(milestone_weeks, milestone_names):
            milestones.append({
                "week": week,
                "milestone": name,
                "verification_method": f"{name} 프로젝트 완성 및 실무 적용 시연"
            })

        return milestones

    def _generate_adaptive_resources(self, subject: str, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """적응형 학습 자료 완전 범용 생성"""

        return [
            {
                "type": "essential",
                "title": f"{subject} 기초 학습 자료",
                "url": f"{subject} 관련 기본 교재 또는 온라인 강의",
                "priority": "high"
            },
            {
                "type": "practice",
                "title": f"{subject} 실습 플랫폼",
                "url": f"{subject} 연습을 위한 온라인 도구나 실습 사이트",
                "priority": "high"
            },
            {
                "type": "community",
                "title": f"{subject} 학습 커뮤니티",
                "url": f"{subject} 관련 온라인 커뮤니티나 학습 그룹",
                "priority": "medium"
            },
            {
                "type": "reference",
                "title": f"{subject} 참고 자료",
                "url": f"{subject} 관련 참고 문서나 가이드",
                "priority": "medium"
            },
            {
                "type": "advanced",
                "title": f"{subject} 심화 학습",
                "url": f"{subject} 고급 과정이나 전문 자료",
                "priority": "low"
            }
        ]

    def _build_prompt(self, request: StudyPlanRequest) -> str:
        """기존 호환성을 위한 프롬프트 (deprecated)"""
        return self._build_universal_prompt(request)

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