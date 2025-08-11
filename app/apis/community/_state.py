from datetime import timezone, timedelta
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

# mock 상태 저장소 (실DB 전환 시 제거)
post_author_map: dict[int, int] = {}
recruit_end_cache: dict[int, object] = {}
post_views: dict[tuple[str, int], int] = {}
post_likes: dict[tuple[int, int], bool] = {}
post_like_counts: dict[int, int] = {}

# 알림 매니저는 너희 프로젝트의 실제 위치로 임포트 교체
# from app.core.notifications import notification_manager
class _DummyNotifier:
    def send_notification(self, user_id: int, message: str):
        print(f"[notify] to={user_id} msg={message}")
notification_manager = _DummyNotifier()
