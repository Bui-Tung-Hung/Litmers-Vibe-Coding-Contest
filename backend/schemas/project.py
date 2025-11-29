from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(ProjectBase):
    pass


class Project(ProjectBase):
    id: int
    team_id: int
    owner_id: int
    is_archived: bool
    is_favorite: bool = False
    issue_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProjectDetail(Project):
    issue_stats: dict


class ArchiveProject(BaseModel):
    is_archived: bool


class LabelBase(BaseModel):
    name: str
    color: str


class LabelCreate(LabelBase):
    pass


class Label(LabelBase):
    id: int
    project_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
