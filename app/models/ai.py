from tortoise import fields, Model
from app.models.base_model import BaseModel


class AIStudyPlan(Model, BaseModel):
    user = fields.ForeignKeyField("models.UserModel", on_delete=fields.CASCADE, null=False) # 유저 식별자 / FK
    is_challenge = fields.BooleanField(default=False, null=False) # 챌린지 여부
    input_data = fields.TextField(null=False)      # 사용자 prompt
    output_data = fields.TextField(null=False)     # AI 생성 학습 계획
    start_date = fields.DatetimeField(null=False)  # 학습 시작일
    end_date = fields.DatetimeField(null=False)    # 학습 종료일

    class Meta:
        table = "ai_study_plans"