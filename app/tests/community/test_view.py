import pytest
from httpx import AsyncClient
from starlette.status import HTTP_200_OK

@pytest.mark.asyncio
class TestPostViews:
    endpoint = "/api/community/post/study"

    async def test_view_count_increases(self, async_client: AsyncClient):
        # 첫 조회
        res1 = await async_client.get(f"{self.endpoint}/1")
        assert res1.status_code == HTTP_200_OK
        data1 = res1.json()
        assert data1["views"] == 1

        # 두 번째 조회
        res2 = await async_client.get(f"{self.endpoint}/1")
        assert res2.status_code == HTTP_200_OK
        data2 = res2.json()
        assert data2["views"] == 2
