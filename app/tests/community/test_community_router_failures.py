import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from pytz import timezone

KST = timezone("Asia/Seoul")

@pytest.mark.asyncio
class TestCommunityRouterFailures:
    endpoint = "/api/community/post"

    # -------- 422: 필수 필드 누락(Study) --------
    async def test_create_study_422_missing_required(self, async_client: AsyncClient):
        # title/content만 보내고 나머지 누락 → Pydantic 422
        resp = await async_client.post(f"{self.endpoint}/study", json={
            "title": "불완전 요청",
            "content": "필수 필드 빠짐",
            "category": "study",
            "user_id": 123
        })
        assert resp.status_code == 422

    # -------- ✅ 자유게시판: 이미지 없이도 성공 --------
    async def test_create_free_without_image_url_success(self, async_client: AsyncClient):
        resp = await async_client.post(f"{self.endpoint}/free", json={
            "title": "이미지 없이 글쓰기",
            "content": "이미지 안 넣었어요",
            "category": "free",
            "user_id": 123
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["category"] == "free"
        assert data["author_id"] == 123
        # 라우터가 free_board.image_url을 항상 포함시키는 구현이므로 None 확인
        assert "free_board" in data and "image_url" in data["free_board"]
        assert data["free_board"]["image_url"] is None

    # -------- ✅ 자료공유: 파일 없이도 성공 --------
    async def test_create_share_without_file_url_success(self, async_client: AsyncClient):
        resp = await async_client.post(f"{self.endpoint}/share", json={
            "title": "파일 없이 글쓰기",
            "content": "파일 안 넣었어요",
            "category": "share",
            "user_id": 456
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["category"] == "share"
        assert data["author_id"] == 456
        assert "data_share" in data and "file_url" in data["data_share"]
        assert data["data_share"]["file_url"] is None

    # -------- 404: 존재하지 않는 글 수정(Free) --------
    async def test_update_free_404_not_found(self, async_client: AsyncClient):
        resp = await async_client.put(f"{self.endpoint}/free/999999", json={
            "title": "수정",
            "content": "수정",
            "category": "free",
            "user_id": 1,
            "image_url": "http://example.com/x.png"
        })
        assert resp.status_code == 404

    # -------- 404: 존재하지 않는 글 수정(Share) --------
    async def test_update_share_404_not_found(self, async_client: AsyncClient):
        resp = await async_client.put(f"{self.endpoint}/share/999999", json={
            "title": "수정",
            "content": "수정",
            "category": "share",
            "user_id": 1,
            "file_url": "http://example.com/x.pdf"
        })
        assert resp.status_code == 404

    # -------- 404: 존재하지 않는 글 삭제 --------
    async def test_delete_404_not_found(self, async_client: AsyncClient):
        resp = await async_client.delete(f"{self.endpoint}/999999")
        assert resp.status_code == 404

    # -------- 403: 스터디 마감 후 '수정' 금지 --------
    async def test_update_study_403_after_deadline(self, async_client: AsyncClient):
        now = datetime.now(KST)
        create = await async_client.post(f"{self.endpoint}/study", json={
            "title": "마감 테스트",
            "content": "마감 후 수정 금지",
            "category": "study",
            "user_id": 777,
            "recruit_start": (now - timedelta(days=3)).isoformat(),
            "recruit_end":   (now - timedelta(days=1)).isoformat(),  # 이미 마감
            "study_start":   (now + timedelta(days=5)).isoformat(),
            "study_end":     (now + timedelta(days=10)).isoformat(),
            "max_member": 5
        })
        assert create.status_code == 200
        post_id = create.json()["id"]

        resp = await async_client.put(f"{self.endpoint}/study/{post_id}", json={
            "title": "수정 시도"
        })
        assert resp.status_code == 403

    # -------- 403: 스터디 마감 후 '신청' 금지 --------
    async def test_join_study_403_after_deadline(self, async_client: AsyncClient):
        now = datetime.now(KST)
        create = await async_client.post(f"{self.endpoint}/study", json={
            "title": "참여 마감 테스트",
            "content": "마감 후 참여 금지",
            "category": "study",
            "user_id": 888,
            "recruit_start": (now - timedelta(days=3)).isoformat(),
            "recruit_end":   (now - timedelta(days=1)).isoformat(),  # 이미 마감
            "study_start":   (now + timedelta(days=5)).isoformat(),
            "study_end":     (now + timedelta(days=10)).isoformat(),
            "max_member": 5
        })
        assert create.status_code == 200
        post_id = create.json()["id"]

        resp = await async_client.post(f"{self.endpoint}/study/{post_id}/join", json={
            "user_id": 999
        })
        assert resp.status_code == 403
