from starlette.status import HTTP_200_OK

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

    async def test_api_create_community_study(self, async_client):
        response = await async_client.post(f"{self.endpoint}/study", json={
            "title": "스터디 모집",
            "content": "선착순으로 모집합니다~",
            "category": "study",
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

    async def test_api_create_community_free(self, async_client):
        response = await async_client.post(f"{self.endpoint}/free", json={
            "title": "소름",
            "content": "지금 시간 새벽2시 22분 진짜임",
            "category": "free",
            "image_url": "http://example.com/test.png"
        })

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["category"] == "free"
        assert data["free_board"]["image_url"].endswith(".png")

    async def test_api_create_community_share(self, async_client):
        response = await async_client.post(f"{self.endpoint}/share", json={
            "title": "자료 공유합니다",
            "content": "속았쥬?",
            "category": "share",
            "file_url": "http://example.com/test.pdf"
        })

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["category"] == "share"
        assert data["data_share"]["file_url"].endswith(".pdf")
