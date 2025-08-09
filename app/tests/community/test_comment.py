import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestComment:
    endpoint = "/api/community/post/1/comment"

    async def test_create_comment(self, async_client: AsyncClient):
        """일반 댓글 생성"""
        body = {
            "post_id": 1,
            "content": "첫 댓글입니다",
            "user_id": 123
        }

        response = await async_client.post(self.endpoint, json=body)
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == body["content"]
        assert data["parent_id"] is None
        assert data["author_id"] == body["user_id"]
        assert "id" in data
        assert "created_at" in data

    async def test_create_reply(self, async_client: AsyncClient):
        """대댓글 생성"""
        body = {
            "post_id": 1,
            "content": "대댓글입니다",
            "parent_id": 1,
            "user_id": 123
        }

        response = await async_client.post(self.endpoint, json=body)
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == body["content"]
        assert data["parent_id"] == body["parent_id"]
        assert data["author_id"] == body["user_id"]
        assert "id" in data
        assert "created_at" in data
