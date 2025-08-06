import pytest
from datetime import datetime
from httpx import AsyncClient

@pytest.mark.asyncio
class TestComment:
    endpoint = "/api/community/post/1/comment"

    async def test_create_comment(self, async_client: AsyncClient):
        """일반 댓글 생성"""
        response = await async_client.post(self.endpoint, json={
            "post_id": 1,
            "content": "첫 댓글입니다"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "첫 댓글입니다"
        assert data["parent_id"] is None

    async def test_create_reply(self, async_client: AsyncClient):
        """대댓글 생성"""
        response = await async_client.post(self.endpoint, json={
            "post_id": 1,
            "content": "대댓글입니다",
            "parent_id": 1
        })
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "대댓글입니다"
        assert data["parent_id"] == 1
