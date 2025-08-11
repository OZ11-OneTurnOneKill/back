from tortoise.models import Model
from tortoise import fields
from app.models.base_model import BaseModel


class StudyPlan(Model, BaseModel):
    """AI 학습계획 테이블"""

    user_id = fields.ForeignKeyField(description="유저 식별자 / FK")
    is_challenge = fields.BooleanField(default=False, description="챌린지 수행 여부")
    input_data = fields.TextField(description="유저 질문 (프롬프트)")
    output_data = fields.TextField(null=True, description="AI 답변")
    start_date = fields.DatetimeField(description="공부 계획 일정 시작하는 날")
    end_date = fields.DatetimeField(description="공부 계획 일정 끝나는 날")

    class Meta:
        table = "ai_study_plans"

    def __str__(self):
        return f"<StudyPlan(id={self.id}, user_id={self.user_id}, is_challenge={self.is_challenge})>"


class ChallengeProgress(Model, BaseModel):
    """AI 챌린지 진행상황 테이블"""

    study_plan = fields.ForeignKeyField(
        "models.StudyPlan",
        related_name="challenge_progress",
        on_delete=fields.CASCADE,
        description="공부 계획 식별자 / FK"
    )
    user_id = fields.ForeignKeyField(description="유저 식별자 / FK")
    status = fields.CharField(
        max_length=50,
        null=True,
        description="챌린지 진행 상태 (진행 완료, 진행 중, 실패)"
    )
    challenge_image_url = fields.TextField(
        null=True,
        description="챌린지 관련 이미지 저장"
    )

    class Meta:
        table = "ai_challenge_progress"

    def __str__(self):
        return f"<ChallengeProgress(id={self.id}, study_plan_id={self.study_plan_id}, status={self.status})>"