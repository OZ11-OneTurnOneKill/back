from enum import Enum
from tortoise import fields, Model
from app.models.base_model import BaseModel

class CategoryType(str, Enum):
    STUDY = "study"
    FREE = "free"
    SHARE = "share"


class ApplicationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class NotificationType(str, Enum):
    application = "application"
    like = "like"


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


class FreeImageModel(BaseModel, Model):
    """자유게시판 이미지 첨부 (1:N)"""
    post = fields.ForeignKeyField(
        "models.PostModel",
        related_name="free_images",
        on_delete=fields.CASCADE,
        index=True,
        null=False,
    )
    image_url  = fields.TextField(null=False)
    image_key  = fields.TextField(null=False)   # S3 key (삭제/교체에 필요)
    mime_type  = fields.CharField(max_length=100, null=False)
    size_bytes = fields.BigIntField(null=False)

    class Meta:
        table = "free_images"
        # 조회 패턴 고려: post_id 단건/목록 조회 빠르게, 정렬 키로 id도 함께
        indexes = (("post_id",), ("post_id", "id"))

    def __str__(self) -> str:
        return f"<FreeImage id={self.id} post={self.post_id} size={self.size_bytes}>"


class ShareFileModel(BaseModel, Model):
    """자료공유 파일 첨부 (1:N)"""
    post = fields.ForeignKeyField(
        "models.PostModel",
        related_name="share_files",
        on_delete=fields.CASCADE,
        index=True,
        null=False,
    )
    file_url   = fields.TextField(null=False)
    file_key   = fields.TextField(null=False)
    mime_type  = fields.CharField(max_length=150, null=False)
    size_bytes = fields.BigIntField(null=False)

    class Meta:
        table = "share_files"
        indexes = (("post_id",), ("post_id", "id"))

    def __str__(self) -> str:
        return f"<ShareFile id={self.id} post={self.post_id} size={self.size_bytes}>"


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
    status = fields.CharEnumField(ApplicationStatus, default=ApplicationStatus.pending.value, null=False)

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
        null=True,
    )
    post = fields.ForeignKeyField(
        "models.PostModel",
        related_name="notifications",
        on_delete=fields.CASCADE,
        null=True,
    )
    type = fields.CharEnumField(NotificationType)
    message = fields.CharField(max_length=255, null=False)
    is_read = fields.BooleanField(default=False, null=False)

    class Meta:
        table = "notifications"
        indexes = (("user_id", "is_read"), ("application_id",), ("post_id",))

    def __str__(self) -> str:
        return f"<Notification user={self.user_id} app={self.application_id} read={self.is_read}>"


class PostViewDailyModel(Model):
    post = fields.ForeignKeyField(
        "models.PostModel",
        related_name="view_dailies",
        on_delete=fields.CASCADE,
        null=False,
    )
    day = fields.DateField(null=False)
    views = fields.IntField(null=False, default=0)

    class Meta:
        table = "post_view_daily"
        unique_together = (("post", "day"),)      # 같은 글+날짜는 1행
        indexes = (("day",), ("post_id", "day"))  # 조회/기간 합계용 인덱스

    def __str__(self) -> str:
        return f"<PostViewDaily post={self.post_id} day={self.day} views={self.views}>"