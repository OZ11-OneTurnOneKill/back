from fastapi import HTTPException, status
from tortoise.transactions import in_transaction
from tortoise.expressions import F
from tortoise.exceptions import IntegrityError
from app.models.community import PostModel, LikeModel

async def service_get_like_count_by_post_id(*, post_id: int) -> dict:
    post = await PostModel.get_or_none(id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"post_id": post_id, "category": post.category, "like_count": post.like_count}

async def service_toggle_like_by_post_id(*, post_id: int, user_id: int) -> dict:
    async with in_transaction() as tx:
        post = await PostModel.get_or_none(id=post_id).using_db(tx)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        existing = await LikeModel.get_or_none(post_id=post_id, user_id=user_id).using_db(tx)
        if existing:
            await existing.delete(using_db=tx)
            if post.like_count > 0:
                await PostModel.filter(id=post_id).using_db(tx).update(like_count=F("like_count") - 1)
            liked, message = False, "unliked"
        else:
            await LikeModel.create(post_id=post_id, user_id=user_id, using_db=tx)
            await PostModel.filter(id=post_id).using_db(tx).update(like_count=F("like_count") + 1)
            liked, message = True, "liked"

        post = await PostModel.get(id=post_id).using_db(tx)

    return {"post_id": post.id, "category": post.category, "like_count": post.like_count, "liked": liked, "message": message}

async def service_like_status(*, post_id: int, user_id: int) -> dict:
    post = await PostModel.get_or_none(id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    liked = await LikeModel.filter(post_id=post_id, user_id=user_id).exists()
    return {"post_id": post_id, "category": post.category, "like_count": post.like_count, "liked": liked}

async def service_delete_post_by_post_id(*, post_id: int, user_id: int) -> dict:
    async with in_transaction() as tx:
        post = await PostModel.get_or_none(id=post_id).using_db(tx)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not the author")

        await PostModel.filter(id=post_id).using_db(tx).delete()
    return {"post_id": post_id, "category": post.category, "message": "deleted"}
