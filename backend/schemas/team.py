from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from backend.models.team import TeamRole


class TeamBase(BaseModel):
    name: str


class TeamCreate(TeamBase):
    pass


class TeamUpdate(TeamBase):
    pass


class Team(TeamBase):
    id: int
    owner_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class TeamWithRole(Team):
    my_role: TeamRole
    member_count: int
    project_count: int


class TeamMemberBase(BaseModel):
    user_id: int
    role: TeamRole


class TeamMember(TeamMemberBase):
    id: int
    team_id: int
    name: str
    email: str
    profile_image: Optional[str] = None
    joined_at: datetime
    
    class Config:
        from_attributes = True


class TeamInviteCreate(BaseModel):
    email: EmailStr


class TeamInvite(BaseModel):
    id: int
    team_id: int
    email: str
    invited_by: int
    expires_at: datetime
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class RoleChange(BaseModel):
    role: TeamRole
