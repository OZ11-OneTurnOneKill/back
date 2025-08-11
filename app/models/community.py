from enum import Enum
from tortoise import fields, Model
from app.models.base_model import BaseModel

class CategoryType(str, Enum):
    STUDY = "study"
    FREE = "free"
    SHARE = "share"


class ApplicationStatus(str, Enum):
    RECRUITING = "recruiting"
    COMPLETED = "completed"


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
        unique_together = (("post", "user"),)
        indexes = (("post_id",), ("user_id",),)


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


class StudyApplicationModel(BaseModel, Model):
    post = fields.ForeignKeyField(
        "models.PostModel",
        related_name="applications",
        on_delete=fields.CASCADE,
        null=False,
    )
    user = fields.ForeignKeyField(
        "models.UserModel",
        related_name="study_applications",
        on_delete=fields.CASCADE,
        null=False,
    )
    status = fields.CharEnumField(ApplicationStatus, default="recruiting", null=False)

    class Meta:
        table = "study_applications"
        # 같은 유저가 같은 스터디 글에 중복 신청 금지
        unique_together = (("post", "user"),)
        # 조회 성능용 인덱스
        indexes = (("post_id",), ("user_id",), ("status", "post_id"))

    def __str__(self) -> str:
        return f"<StudyApplication post={self.post_id} user={self.user_id} status={self.status}>"


class NotificationModel(BaseModel, Model):
    user = fields.ForeignKeyField(
        "models.UserModel",
        related_name="notifications",
        on_delete=fields.CASCADE,
        null=False,
    )
    application = fields.ForeignKeyField(
        "models.StudyApplicationModel",
        related_name="notifications",
        on_delete=fields.CASCADE,
        null=False,
    )
    message = fields.CharField(max_length=255, null=False)
    is_read = fields.BooleanField(default=False, null=False)

    class Meta:
        table = "notifications"
        indexes = (("user_id", "is_read"), ("application_id",))

    def __str__(self) -> str:
        return f"<Notification user={self.user_id} app={self.application_id} read={self.is_read}>"