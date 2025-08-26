import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from starlette.status import HTTP_200_OK


KST = ZoneInfo("Asia/Seoul")

@pytest.mark.asyncio
class TestPostViews:
    endpoint = "/api/community/post/study"

    async def test_view_count_increases(self, async_client: AsyncClient):
        # ✅ 1. 테스트용 게시글 생성 (뷰 0)
        now = datetime.now(KST)
        create_res = await async_client.post(self.endpoint, json={
            "title": "조회수 테스트",
            "content": "조회수를 올려봅시다",
            "category": "study",
            "user_id": 456,
            "study_start": (now + timedelta(days=3)).isoformat(),
            "study_end": (now + timedelta(days=10)).isoformat(),
            "recruit_start": now.isoformat(),
            "recruit_end": (now + timedelta(days=5)).isoformat(),
            "max_member": 5
        })
        assert create_res.status_code == HTTP_200_OK
        post_id = create_res.json()["id"]

        # ✅ 2. 첫 조회 → views == 1
        res1 = await async_client.get(f"{self.endpoint}/{post_id}")
        assert res1.status_code == HTTP_200_OK
        data1 = res1.json()
        assert data1["views"] == 1

        # ✅ 3. 두 번째 조회 → views == 2
        res2 = await async_client.get(f"{self.endpoint}/{post_id}")
        assert res2.status_code == HTTP_200_OK
        data2 = res2.json()
        assert data2["views"] == 2

        # ✅ 보너스 검증: 필수 응답 필드 존재 여부
        for field in ["id", "title", "content", "category", "author_id", "views", "created_at"]:
            assert field in data2
