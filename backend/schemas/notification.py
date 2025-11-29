from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Notification(BaseModel):
    id: int
    type: str
    title: str
    message: str
    related_issue_id: Optional[int] = None
    related_team_id: Optional[int] = None
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class NotificationList(BaseModel):
    notifications: list[Notification]
    unread_count: int
