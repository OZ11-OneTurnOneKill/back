class NotificationManager:
    def __init__(self):
        self.notifications = []

    def send_notification(self, user_id: int, message: str):
        self.notifications.append({"user_id": user_id, "message": message})

    def get_all(self):
        return self.notifications

    def reset(self):
        self.notifications.clear()

notification_manager = NotificationManager()