from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from backend.models.issue import IssuePriority


class IssueBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: IssuePriority = IssuePriority.MEDIUM
    assignee_id: Optional[int] = None
    due_date: Optional[date] = None


class IssueCreate(IssueBase):
    label_ids: List[int] = []


class IssueUpdate(IssueBase):
    status: Optional[str] = None
    label_ids: Optional[List[int]] = None


class IssuePositionUpdate(BaseModel):
    status: str
    position: int


class UserBrief(BaseModel):
    id: int
    name: str
    profile_image: Optional[str] = None
    
    class Config:
        from_attributes = True


class LabelBrief(BaseModel):
    id: int
    name: str
    color: str
    
    class Config:
        from_attributes = True


class Issue(IssueBase):
    id: int
    project_id: int
    status: str
    position: int
    owner: UserBrief
    assignee: Optional[UserBrief] = None
    labels: List[LabelBrief] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class IssueDetail(Issue):
    ai_summary: Optional[str] = None
    ai_suggestion: Optional[str] = None
    comment_count: int = 0


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    pass


class CommentUpdate(CommentBase):
    pass


class Comment(CommentBase):
    id: int
    issue_id: int
    user: UserBrief
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
