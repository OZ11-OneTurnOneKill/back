import pytest
from httpx import AsyncClient
from starlette.status import HTTP_200_OK

class TestLikes:
    endpoint = "/api/community/post"

    async def test_toggle_like(self, async_client: AsyncClient):
        """좋아요 → 취소 → 다시 좋아요 토글 흐름"""

        # 첫 좋아요 (추가됨)
        res1 = await async_client.post(f"{self.endpoint}/1/like", json={"user_id": 1})
        assert res1.status_code == HTTP_200_OK
        data1 = res1.json()
        assert data1["likes"] == 1
        assert data1["liked"] is True
        assert data1["post_id"] == 1

        # 같은 유저가 다시 누름 (취소됨)
        res2 = await async_client.post(f"{self.endpoint}/1/like", json={"user_id": 1})
        assert res2.status_code == HTTP_200_OK
        data2 = res2.json()
        assert data2["likes"] == 0
        assert data2["liked"] is False
        assert data2["post_id"] == 1

        # 다시 누르면 또 좋아요 추가
        res3 = await async_client.post(f"{self.endpoint}/1/like", json={"user_id": 1})
        assert res3.status_code == HTTP_200_OK  # ✅ 누락된 상태코드 검사 추가
        data3 = res3.json()
        assert data3["likes"] == 1
        assert data3["liked"] is True
        assert data3["post_id"] == 1
