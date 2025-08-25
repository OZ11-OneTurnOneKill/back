from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from tortoise.transactions import in_transaction
from tortoise.expressions import F
from app.models.community import PostModel, LikeModel, CommentModel, NotificationModel, NotificationType
from pytz import timezone
from datetime import datetime
from app.models.user import UserModel
from app.services.community_services.notification_service import notify_like

KST = timezone("Asia/Seoul")


def _cat_val(cat):
    # Enum/str 모두 안전 처리
    return getattr(cat, "value", cat)


async def service_get_like_info(*, post_id: int, user_id: Optional[int] = None) -> dict:
    post = await (
        PostModel.get_or_none(id=post_id, is_active=True)
        .only("id", "category", "like_count")
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    res = {
        "post_id": post_id,
        "category": _cat_val(post.category),
        "like_count": post.like_count,
    }
    if user_id is not None:
        res["liked"] = await LikeModel.filter(post_id=post_id, user_id=user_id).exists()
    return res

async def service_toggle_like_by_post_id(*, post_id: int, user_id: int) -> dict:
    """
    - 트랜잭션 내: Like 토글 + like_count 증감
    - 트랜잭션 밖: 방금 '좋아요'가 된 경우에만 알림 발송 (자기 글이면 스킵)
    """
    just_liked = False
    liked = False

    async with in_transaction() as tx:
        post = await PostModel.get_or_none(id=post_id).using_db(tx)
        if not post or not post.is_active:
            raise HTTPException(status_code=404, detail="Post not found")

        existing = await LikeModel.get_or_none(post_id=post_id, user_id=user_id).using_db(tx)
        if existing:
            # 좋아요 취소
            await existing.delete(using_db=tx)
            await PostModel.filter(id=post_id).using_db(tx).update(
                like_count=F("like_count") - 1
            )
            liked = False
        else:
            # 좋아요 생성
            await LikeModel.create(post_id=post_id, user_id=user_id, using_db=tx)
            await PostModel.filter(id=post_id).using_db(tx).update(
                like_count=F("like_count") + 1
            )
            liked = True
            just_liked = True

        # 최신 카운트/필요 필드 재조회
        post = await PostModel.get(id=post_id).only("like_count", "user_id", "category").using_db(tx)

    # === 트랜잭션 밖: 알림 ===
    if just_liked and post.user_id != user_id:
        # 실패해도 본 로직은 성공이어야 하므로 예외 전파 안 함
        try:
            await notify_like(post_id=post_id, actor_id=user_id)
        except Exception:
            pass

    return {
        "post_id": post_id,
        "category": _cat_val(post.category),
        "like_count": post.like_count,
        "liked": liked,
        "message": "liked" if liked else "unliked",
    }


async def service_delete_post_by_post_id(*, post_id: int, user_id: int) -> dict:
    async with in_transaction() as tx:
        post = await PostModel.get_or_none(id=post_id).using_db(tx)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not the author")

        await PostModel.filter(id=post_id).using_db(tx).delete()
    return {"post_id": post_id, "category": _cat_val(post.category), "message": "deleted"}


def compose_comment_response(c: CommentModel) -> dict:
    nick = getattr(getattr(c, "user", None), "nickname", None)
    return {
        "id": c.id,
        "post_id": c.post_id,
        "content": c.content,
        "author_id": c.user_id,
        "author_nickname": nick,
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

            if parent.parent_comment_id is not None:
                raise HTTPException(status_code=400, detail="Only one-level replies allowed")

        c = await CommentModel.create(
            post_id=post_id, user_id=user_id,
            parent_comment_id=parent_comment_id,
            content=content, using_db=tx
        )

        # (선택) 카운트 관리 중이면 카운트 +1
        await PostModel.filter(id=post_id).using_db(tx).update(comment_count=F("comment_count") + 1)

        # 타임스탬프/필드 최신화 위해 재조회
        c = await CommentModel.get(id=c.id).select_related("user").using_db(tx)

    return compose_comment_response(c)

async def service_list_comments(*, post_id: int, order: str = "id", offset: int = 0, limit: int = 50) -> Dict[str, Any]:
    allowed = {"id", "-id", "created_at", "-created_at"}
    order = order if order in allowed else "id"
    limit = max(1, min(100, limit))

    total = await CommentModel.filter(post_id=post_id).count()
    rows = (await CommentModel
            .filter(post_id=post_id)
            .select_related("user")
            .order_by(order)
            .offset(offset)
            .limit(limit))
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

        c = await CommentModel.get(id=comment_id).select_related("user").using_db(tx)

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