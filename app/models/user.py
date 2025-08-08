from enum import Enum
from tortoise import fields, Model
from app.models.base_model import BaseModel

class ProviderType(str, Enum):
    GOOGLE = "google"
    KAKAO = "kakao"

class UserModel(BaseModel, Model):
    social_account = fields.ForeignKeyField(
        "models.SocialAccountModel",
        related_name="users",
        on_delete=fields.CASCADE,
        null=False
    )
    nickname = fields.CharField(max_length=8, unique=True, null=False)
    profile_image_url = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True, null=False)
    is_superuser = fields.BooleanField(default=False, null=False)
    class Meta:
        table = "users"

class SocialAccountModel(BaseModel, Model):
    provider = fields.CharEnumField(ProviderType, null=False)
    provider_id = fields.CharField(max_length=50, null=False, unique=True)
    email = fields.CharField(max_length=50, null=False, unique=True)
    class Meta:
        table = "social_accounts"

class RefreshTokenModel(BaseModel, Model):
    user = fields.ForeignKeyField(
        "models.UserModel",
        related_name="refresh_tokens",
        on_delete=fields.CASCADE,
        null=False
    )
    token = fields.TextField(null=False)
    expires_at = fields.DatetimeField(null=False)
    revoked = fields.BooleanField(default=False, null=False)
    class Meta:
        table = "refresh_tokens"