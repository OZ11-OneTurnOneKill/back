from enum import Enum
from tortoise import fields, models
from app.models.base_model import BaseModel

class ProviderType(str, Enum):
    GOOGLE = "google"
    KAKAO = "kakao"

class UserModel(BaseModel, models):
    social_account = fields.BigIntField
    nickname = fields.CharField(max_length=8, unique=True, null=False)
    profile_image_url = fields.CharField(max_length=255, null=True)
    is_active = fields.BooleanField(default=True, null=False)
    is_superuser = fields.BooleanField(default=False, null=False)

class SocialAccountModel(BaseModel, models):
    provider = fields.CharEnumField(ProviderType, null=False)
    provider_id = fields.CharField(max_length=50, null=False, unique=True)
    email = fields.CharField(max_length=50, null=False, unique=True)

