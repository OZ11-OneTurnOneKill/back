from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from tortoise.transactions import in_transaction
from tortoise.expressions import F
from tortoise.exceptions import IntegrityError

from app.core.realtime import notification_broker
from app.models.community import PostModel, LikeModel, CommentModel, NotificationModel, NotificationType
from pytz import timezone
from datetime import datetime


KST = timezone("Asia/Seoul")


def _val(x):
    # Enum -> value, 나머지는 안전한 타입으로
    if hasattr(x, "value"):
        return x.value
    return x


async def service_get_like_info(*, post_id: int, user_id: Optional[int] = None) -> dict:
    post = await (
        PostModel.get_or_none(id=post_id, deleted_at__isnull=True)
        .only("id", "category", "like_count")
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    res = {
        "post_id": post_id,
        "category": post.category,
        "like_count": post.like_count,
    }
    if user_id is not None:
        res["liked"] = await LikeModel.filter(post_id=post_id, user_id=user_id).exists()
    return res

async def service_toggle_like_by_post_id(*, post_id: int, user_id: int) -> dict:
    note_payload = None

    async with in_transaction() as tx:
        post = await PostModel.get_or_none(id=post_id).using_db(tx)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        existing = await LikeModel.get_or_none(post_id=post_id, user_id=user_id).using_db(tx)
        if existing:
            await existing.delete(using_db=tx)
            await PostModel.filter(id=post_id).using_db(tx).update(like_count=F("like_count") - 1)
            liked, message = False, "unliked"
        else:
            await LikeModel.create(post_id=post_id, user_id=user_id, using_db=tx)
            await PostModel.filter(id=post_id).using_db(tx).update(like_count=F("like_count") + 1)
            liked, message = True, "liked"

            # (알림 쓰는 경우) 본인 글이 아니면 저장/푸시
            if hasattr(post, "user_id") and post.user_id != user_id:
                try:
                    note = await NotificationModel.create(
                        user_id=post.user_id,
                        post_id=post_id,
                        application_id=None,
                        type=_val(NotificationType.like),   # ← Enum 안전 변환
                        message=f"사용자 {user_id}님이 게시글({post_id})에 좋아요를 눌렀습니다.",
                        using_db=tx,
                    )
                    note_payload = {
                        "target_user_id": post.user_id,
                        "data": {
                            "id": note.id,
                            "type": _val(note.type),         # ← Enum 안전 변환
                            "post_id": post_id,
                            "message": note.message,
                            "is_read": note.is_read,
                            "created_at": note.created_at,
                        },
                    }
                except Exception:
                    note_payload = None

        # 필요한 필드만 재조회
        post = await PostModel.get(id=post_id).only("category", "like_count").using_db(tx)

    # 커밋 후 푸시
    if note_payload:
        try:
            await notification_broker.push(note_payload["target_user_id"], note_payload["data"])
        except Exception:
            pass

    return {
        "post_id": post_id,
        "category": _val(post.category.value),   # ← Enum이면 .value 로
        "like_count": post.like_count,
        "liked": liked,
        "message": message,
    }

async def service_delete_post_by_post_id(*, post_id: int, user_id: int) -> dict:
    async with in_transaction() as tx:
        post = await PostModel.get_or_none(id=post_id).using_db(tx)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not the author")

        await PostModel.filter(id=post_id).using_db(tx).delete()
    return {"post_id": post_id, "category": post.category, "message": "deleted"}


def compose_comment_response(c: CommentModel) -> dict:
    return {
        "id": c.id,
        "post_id": c.post_id,
        "content": c.content,
        "author_id": c.user_id,
        "parent_id": c.parent_comment_id,   # ← 응답 DTO의 필드명(parent_id)로 맞춤
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }

async def service_create_comment(*, post_id: int, user_id: int, content: str, parent_comment_id: Optional[int]):
    async with in_transaction() as tx:
        post = await PostModel.get_or_none(id=post_id).using_db(tx)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        if parent_comment_id is not None:
            parent = await CommentModel.get_or_none(id=parent_comment_id).using_db(tx)
            if not parent or parent.post_id != post_id:
                raise HTTPException(status_code=400, detail="Invalid parent_comment_id")

        c = await CommentModel.create(
            post_id=post_id, user_id=user_id,
            parent_comment_id=parent_comment_id,
            content=content, using_db=tx
        )

        # (선택) 카운트 관리 중이면 카운트 +1
        await PostModel.filter(id=post_id).using_db(tx).update(comment_count=F("comment_count") + 1)

        # 타임스탬프/필드 최신화 위해 재조회
        c = await CommentModel.get(id=c.id).using_db(tx)

    return compose_comment_response(c)

async def service_list_comments(*, post_id: int, order: str = "id", offset: int = 0, limit: int = 50) -> Dict[str, Any]:
    total = await CommentModel.filter(post_id=post_id).count()
    rows = await CommentModel.filter(post_id=post_id).order_by(order).offset(offset).limit(limit)
    items = [compose_comment_response(r) for r in rows]
    return {"total": total, "count": len(items), "items": items}

async def service_update_comment(*, comment_id: int, user_id: int, content: str) -> Dict[str, Any]:
    async with in_transaction() as tx:
        c = await CommentModel.get_or_none(id=comment_id).using_db(tx)
        if not c:
            raise HTTPException(status_code=404, detail="Comment not found")
        if c.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not the author")

        c.content = content
        await c.save(using_db=tx)

    return compose_comment_response(c)

# parent_comment 가 CASCADE라 부모 삭제 시 자식도 함께 삭제됨
# -> 포스트 comment_count를 정확히 맞추려면 '삭제될 총 개수'를 미리 계산해서 깎아야 함
async def _count_descendants(root_id: int) -> int:
    """root 포함하지 않음. 모든 자식/후손 개수."""
    to_visit = [root_id]
    descendants = 0
    while to_visit:
        batch = to_visit
        to_visit = []
        # 이 배치의 자식들
        children = await CommentModel.filter(parent_comment_id__in=batch).values_list("id", flat=True)
        if not children:
            continue
        descendants += len(children)
        to_visit.extend(children)
    return descendants


async def service_delete_comment(*, comment_id: int, user_id: int) -> Dict[str, Any]:
    async with in_transaction() as tx:
        c = await CommentModel.get_or_none(id=comment_id).using_db(tx)
        if not c:
            raise HTTPException(status_code=404, detail="Comment not found")
        if c.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not the author")

        post_id = c.post_id

        # CASCADE로 지워질 전체 개수 계산: root(1) + 모든 후손
        descendants = await _count_descendants(comment_id)
        total_to_delete = 1 + descendants

        # 실제 삭제 (CASCADE로 자식도 함께 삭제)
        await c.delete(using_db=tx)

        # 포스트 댓글 카운트 조정 (바닥 보호)
        post = await PostModel.get_or_none(id=post_id).using_db(tx)
        if post:
            dec = min(post.comment_count, total_to_delete)
            await PostModel.filter(id=post_id).using_db(tx).update(comment_count=F("comment_count") - dec)

    return {"id": comment_id, "deleted": True}