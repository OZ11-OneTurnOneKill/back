from datetime import datetime, timedelta
from httpx import AsyncClient
from zoneinfo import ZoneInfo
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, HTTP_422_UNPROCESSABLE_ENTITY

KST = ZoneInfo("Asia/Seoul")

class TestStudyPost:
    endpoint = "/api/community/post/study"

    async def test_create_study_post_valid(self, async_client: AsyncClient):
        now = datetime.now(KST)
        response = await async_client.post(self.endpoint, json={
            "title": "파이썬 스터디 모집",
            "content": "매주 주말 스터디",
            "category": "study",
            "user_id": 123,
            "study_start": (now + timedelta(days=10)).isoformat(),
            "study_end": (now + timedelta(days=40)).isoformat(),
            "recruit_start": now.isoformat(),
            "recruit_end": (now + timedelta(days=7)).isoformat(),
            "max_member": 10
        })

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["category"] == "study"
        assert data["study_recruitment"]["max_member"] == 10
        assert data["author_id"] == 123
        assert "id" in data and "views" in data and "created_at" in data

    async def test_invalid_study_period(self, async_client: AsyncClient):
        now = datetime.now(KST)
        response = await async_client.post(self.endpoint, json={
            "title": "잘못된 스터디 모집",
            "content": "스터디 기간 에러",
            "category": "study",
            "user_id": 123,
            "study_start": now.isoformat(),
            "study_end": (now - timedelta(days=1)).isoformat(),
            "recruit_start": now.isoformat(),
            "recruit_end": (now + timedelta(days=7)).isoformat(),
            "max_member": 5
        })

        assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY
        assert "스터디 종료일은 시작일 이후여야 합니다" in response.text

    async def test_invalid_recruit_period(self, async_client: AsyncClient):
        now = datetime.now(KST)
        response = await async_client.post(self.endpoint, json={
            "title": "잘못된 구인 모집",
            "content": "구인 기간 에러",
            "category": "study",
            "user_id": 123,
            "study_start": (now + timedelta(days=10)).isoformat(),
            "study_end": (now + timedelta(days=20)).isoformat(),
            "recruit_start": now.isoformat(),
            "recruit_end": (now - timedelta(days=1)).isoformat(),
            "max_member": 5
        })

        assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY
        assert "구인 마감일은 시작일 이후여야 합니다" in response.text

    async def test_post_after_recruit_end(self, async_client: AsyncClient):
        now = datetime.now(KST)
        # 마감된 스터디 글 생성
        response = await async_client.post(self.endpoint, json={
            "title": "마감된 스터디",
            "content": "이미 마감된 스터디",
            "category": "study",
            "user_id": 123,
            "study_start": (now + timedelta(days=5)).isoformat(),
            "study_end": (now + timedelta(days=15)).isoformat(),
            "recruit_start": (now - timedelta(days=10)).isoformat(),
            "recruit_end": (now - timedelta(days=5)).isoformat(),  # 이미 마감
            "max_member": 5
        })
        assert response.status_code == HTTP_200_OK
        data = response.json()
        post_id = data["id"]

        # 조회 가능
        res_view = await async_client.get(f"{self.endpoint}/{post_id}")
        assert res_view.status_code == HTTP_200_OK

        # 수정 불가
        res_edit = await async_client.put(f"{self.endpoint}/{post_id}", json={
            "title": "수정 시도"
        })
        assert res_edit.status_code == HTTP_403_FORBIDDEN

        # 참여 불가
        res_join = await async_client.post(f"{self.endpoint}/{post_id}/join", json={"user_id": 99})
        assert res_join.status_code in (HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN)