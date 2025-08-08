from enum import Enum
from tortoise import fields, Model
from app.models.base_model import BaseModel

class CategoryType(str, Enum):
    STUDY = "study"
    FREE = "free"
    SHARE = "share"

class PostModel(BaseModel, Model):
    user = fields.ForeignKeyField(
        "models.UserModel",
        related_name="posts",
        on_delete=fields.CASCADE,
        null=False
    )
    title = fields.CharField(max_length=20, null=False)
    content = fields.CharField(max_length=500, null=False)
    category = fields.CharEnumField(CategoryType, null=False)
    view_count = fields.BigIntField(null=False, default=0)
    like_count = fields.BigIntField(null=False, default=0)
    comment_count = fields.BigIntField(null=False, default=0)
    is_active = fields.BooleanField(null=False, default=True)
    deleted_at = fields.DatetimeField(null=True)
    class Meta:
        table = "posts"


class CommentModel(BaseModel, Model):
    user = fields.ForeignKeyField(
        "models.UserModel",
        related_name="comments",
        on_delete=fields.CASCADE,
        null=False
    )
    post = fields.ForeignKeyField(
        "models.PostModel",
        related_name="comments",
        on_delete=fields.CASCADE,
        null=False
    )
    content = fields.CharField(max_length=50, null=False)
    parent_comment = fields.ForeignKeyField(
        "models.CommentModel",
        related_name="child_comments",
        on_delete=fields.CASCADE,
        null=True
    )
    class Meta:
        table = "comments"


class LikeModel(BaseModel, Model):
    user = fields.ForeignKeyField(
        "models.UserModel",
        related_name="likes",
        on_delete=fields.CASCADE,
        null=False
    )
    post = fields.ForeignKeyField(
        "models.PostModel",
        related_name="likes",
        on_delete=fields.CASCADE,
        null=False
    )
    class Meta:
        table = "likes"


class StudyRecruitmentModel(Model):
    post = fields.OneToOneField(
        "models.PostModel",
        related_name="study_recruitment",
        on_delete=fields.CASCADE,
        pk=True
    )
    recruit_start = fields.DatetimeField(null=False)
    recruit_end = fields.DatetimeField(null=False)
    study_start = fields.DatetimeField(null=False)
    study_end = fields.DatetimeField(null=False)
    max_member = fields.IntField(null=False)
    class Meta:
        table = "study_recruitments"


class FreeBoardModel(Model):
    post = fields.OneToOneField(
        "models.PostModel",
        related_name="free_board",
        on_delete=fields.CASCADE,
        pk=True
    )
    image_url = fields.TextField(null=True)
    class Meta:
        table = "free_boards"


class DataShareModel(Model):
    post = fields.OneToOneField(
        "models.PostModel",
        related_name="data_share",
        on_delete=fields.CASCADE,
        pk=True
    )
    file_url = fields.TextField(null=True)
    class Meta:
        table = "data_shares"