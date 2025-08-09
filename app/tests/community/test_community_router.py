from starlette.status import HTTP_200_OK
from httpx import AsyncClient


class TestCommunityRouter:
    endpoint = "/api/community/post"

    # async def test_api_create_community(self, async_client):
    #     response = await async_client.post(self.endpoint, json={
    #         "title": "공통 속성 테스트",
    #         "content": "공통 내용 테스트",
    #         "category": "study"
    #     })
    #
    #     assert response.status_code == HTTP_200_OK
    #     data = response.json()
    #     assert data["title"] == "공통 속성 테스트"
    #     assert data["content"] == "공통 내용 테스트"
    #     assert data["category"] in ["study", "free", "share"]

    async def test_api_create_community_study(self, async_client: AsyncClient):
        response = await async_client.post(f"{self.endpoint}/study", json={
            "title": "스터디 모집",
            "content": "선착순으로 모집합니다~",
            "category": "study",
            "user_id": 123,
            "recruit_start": "2025-08-01T00:00:00",
            "recruit_end": "2025-08-05T00:00:00",
            "study_start": "2025-08-06T00:00:00",
            "study_end": "2025-08-10T00:00:00",
            "max_member": 5
        })

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["category"] == "study"
        assert data["study_recruitment"]["max_member"] == 5
        assert data["author_id"] == 123
        assert "id" in data and "views" in data and "created_at" in data

    async def test_api_create_community_free(self, async_client: AsyncClient):
        response = await async_client.post(f"{self.endpoint}/free", json={
            "title": "소름",
            "content": "지금 시간 새벽2시 22분 진짜임",
            "category": "free",
            "image_url": "http://example.com/test.png",
            "user_id": 123
        })

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["category"] == "free"
        assert data["free_board"]["image_url"].endswith(".png")
        assert data["author_id"] == 123
        assert "id" in data and "views" in data and "created_at" in data

    async def test_api_create_community_share(self, async_client: AsyncClient):
        response = await async_client.post(f"{self.endpoint}/share", json={
            "title": "자료 공유합니다",
            "content": "속았쥬?",
            "category": "share",
            "file_url": "http://example.com/test.pdf",
            "user_id": 123
        })

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["category"] == "share"
        assert data["data_share"]["file_url"].endswith(".pdf")
        assert data["author_id"] == 123
        assert "id" in data and "views" in data and "created_at" in data

# 스터디 게시판 수정 테스트
    async def test_api_update_community_study(self, async_client: AsyncClient):
        # 1) 먼저 생성
        create = await async_client.post(f"{self.endpoint}/study", json={
            "title": "스터디 모집",
            "content": "선착순으로 모집합니다~",
            "category": "study",
            "user_id": 123,
            "recruit_start": "2025-08-01T00:00:00",
            "recruit_end": "2025-08-15T00:00:00",  # 마감 지나지 않게
            "study_start": "2025-08-16T00:00:00",
            "study_end": "2025-08-20T00:00:00",
            "max_member": 5
        })
        assert create.status_code == 200
        post_id = create.json()["id"]

        # 2) 업데이트
        resp = await async_client.put(f"{self.endpoint}/study/{post_id}", json={
            "title": "제목 수정됨",
            "content": "내용 수정됨",
            "recruit_start": "2025-08-02T00:00:00",
            "recruit_end": "2025-08-18T00:00:00",
            "study_start": "2025-08-19T00:00:00",
            "study_end": "2025-08-25T00:00:00",
            "max_member": 10
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "제목 수정됨"
        assert data["study_recruitment"]["max_member"] == 10
        assert data["category"] == "study"
        assert data["author_id"] == 123
        assert "updated_at" in data

# 잡담 게시판 수정 테스트
    async def test_api_update_community_free(self, async_client: AsyncClient):
        # 1) 생성
        create = await async_client.post(f"{self.endpoint}/free", json={
            "title": "소름",
            "content": "지금 시간 새벽2시 22분 진짜임",
            "category": "free",
            "image_url": "http://example.com/test.png",
            "user_id": 123
        })
        assert create.status_code == 200
        post_id = create.json()["id"]

        # 2) 업데이트
        resp = await async_client.put(f"{self.endpoint}/free/{post_id}", json={
            "title": "자유 글 수정",
            "content": "내용 수정",
            "category": "free",
            "user_id": 123,
            "image_url": "http://example.com/changed.png"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "자유 글 수정"
        assert data["free_board"]["image_url"].endswith(".png")
        assert data["author_id"] == 123
        assert "updated_at" in data

# 자료공유 게시판 수정 테스트
    async def test_api_update_community_share(self, async_client: AsyncClient):
        # 1) 생성
        create = await async_client.post(f"{self.endpoint}/share", json={
            "title": "자료 공유합니다",
            "content": "속았쥬?",
            "category": "share",
            "file_url": "http://example.com/test.pdf",
            "user_id": 123
        })
        assert create.status_code == 200
        post_id = create.json()["id"]

        # 2) 업데이트
        resp = await async_client.put(f"{self.endpoint}/share/{post_id}", json={
            "title": "자료 공유 수정",
            "content": "내용 수정",
            "category": "share",
            "file_url": "http://example.com/changed.pdf",
            "user_id": 123
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "자료 공유 수정"
        assert data["data_share"]["file_url"].endswith(".pdf")
        assert data["author_id"] == 123
        assert "updated_at" in data

# 게시글 삭제 테스트
    async def test_api_delete_post_then_404(self, async_client: AsyncClient):
        # 1) 생성(카테고리는 상관 X)
        create = await async_client.post(f"{self.endpoint}/free", json={
            "title": "삭제 대상",
            "content": "지워질 글",
            "category": "free",
            "image_url": "http://example.com/test.png",
            "user_id": 999
        })
        assert create.status_code == 200
        post_id = create.json()["id"]

        # 2) 삭제
        resp = await async_client.delete(f"{self.endpoint}/{post_id}")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

        # 3) 재삭제 → 404
        resp2 = await async_client.delete(f"{self.endpoint}/{post_id}")
        assert resp2.status_code == 404