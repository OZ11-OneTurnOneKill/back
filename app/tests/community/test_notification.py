import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from app.services.notification_manager import notification_manager
from pytz import timezone

KST = timezone("Asia/Seoul")

class TestNotification:
    endpoint = "/api/community/post/study/1/join"

    async def test_notification_sent_on_study_join(self, async_client: AsyncClient):
        notification_manager.reset()
        now = datetime.now(KST)

        # ✅ 스터디 게시글 생성
        create_res = await async_client.post("/api/community/post/study", json={
            "title": "스터디 모집",
            "content": "내용",
            "category": "study",
            "study_start": (now + timedelta(days=10)).isoformat(),
            "study_end": (now + timedelta(days=20)).isoformat(),
            "recruit_start": (now - timedelta(days=1)).isoformat(),
            "recruit_end": (now + timedelta(days=5)).isoformat(),
            "max_member": 5,
            "user_id": 123
        })
        assert create_res.status_code == 200
        post_id = create_res.json()["id"]

        # ✅ 신청자는 다른 유저
        res = await async_client.post(f"/api/community/post/study/{post_id}/join", json={"user_id": 99})
        assert res.status_code == 200

        # ✅ 알림 검증
        notifications = notification_manager.get_all()
        assert len(notifications) == 1
        assert notifications[0]["user_id"] == 123
        assert str(99) in notifications[0]["message"]
        assert "참여" in notifications[0]["message"]

    async def test_notification_sent_on_like(self, async_client: AsyncClient):
        notification_manager.reset()

        # ✅ 게시글 생성
        create_res = await async_client.post("/api/community/post/free", json={
            "title": "좋아요 알림 테스트",
            "content": "내용",
            "category": "free",
            "user_id": 111
        })
        assert create_res.status_code == 200
        post_id = create_res.json()["id"]

        # ✅ 좋아요 누름
        like_res = await async_client.post(f"/api/community/post/{post_id}/like", json={"user_id": 42})
        assert like_res.status_code == 200

        # ✅ 알림 검증
        notifications = notification_manager.get_all()
        assert len(notifications) == 1
        assert notifications[0]["user_id"] == 111
        assert "좋아요" in notifications[0]["message"]
        assert str(42) in notifications[0]["message"]