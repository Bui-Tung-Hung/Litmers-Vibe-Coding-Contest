from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend.models.user import User
from backend.models.team import Team, TeamMember
from backend.models.project import Project, ProjectFavorite
from backend.models.issue import Issue, Comment
from backend.dependencies import get_current_user
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class IssueBrief(BaseModel):
    id: int
    title: str
    due_date: Optional[str]
    project_name: str
    status: str


class CommentBrief(BaseModel):
    id: int
    issue_title: str
    content: str
    created_at: datetime


class TeamBrief(BaseModel):
    id: int
    name: str
    role: str


class ProjectBrief(BaseModel):
    id: int
    name: str
    team_name: str
    issue_count: int


class PersonalDashboard(BaseModel):
    my_issues: dict
    due_soon: List[IssueBrief]
    recent_comments: List[CommentBrief]
    my_teams: List[TeamBrief]
    my_projects: List[ProjectBrief]


class ProjectDashboard(BaseModel):
    issue_stats: dict
    completion_rate: float
    priority_stats: dict
    recent_issues: List[IssueBrief]
    due_soon: List[IssueBrief]


@router.get("/personal", response_model=PersonalDashboard)
def get_personal_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personal dashboard data"""
    # My issues grouped by status
    my_issues = {}
    issues_by_status = db.query(Issue.status, func.count(Issue.id)).filter(
        Issue.assignee_id == current_user.id,
        Issue.deleted_at.is_(None)
    ).group_by(Issue.status).all()
    
    for status, count in issues_by_status:
        my_issues[status] = count
    
    # Due soon (within 7 days)
    seven_days_later = datetime.utcnow().date() + timedelta(days=7)
    due_soon_issues = db.query(Issue, Project).join(
        Project, Project.id == Issue.project_id
    ).filter(
        Issue.assignee_id == current_user.id,
        Issue.due_date.isnot(None),
        Issue.due_date <= seven_days_later,
        Issue.deleted_at.is_(None)
    ).order_by(Issue.due_date.asc()).limit(5).all()
    
    due_soon = []
    for issue, project in due_soon_issues:
        due_soon.append({
            "id": issue.id,
            "title": issue.title,
            "due_date": str(issue.due_date),
            "project_name": project.name,
            "status": issue.status
        })
    
    # Recent comments
    recent_comments_data = db.query(Comment, Issue).join(
        Issue, Issue.id == Comment.issue_id
    ).filter(
        Comment.user_id == current_user.id,
        Comment.deleted_at.is_(None)
    ).order_by(Comment.created_at.desc()).limit(5).all()
    
    recent_comments = []
    for comment, issue in recent_comments_data:
        recent_comments.append({
            "id": comment.id,
            "issue_title": issue.title,
            "content": comment.content[:100],
            "created_at": comment.created_at
        })
    
    # My teams
    my_teams_data = db.query(Team, TeamMember.role).join(
        TeamMember, TeamMember.team_id == Team.id
    ).filter(
        TeamMember.user_id == current_user.id,
        Team.deleted_at.is_(None)
    ).all()
    
    my_teams = []
    for team, role in my_teams_data:
        my_teams.append({
            "id": team.id,
            "name": team.name,
            "role": role.value
        })
    
    # My projects (from teams)
    my_projects_data = db.query(Project, Team).join(
        Team, Team.id == Project.team_id
    ).join(
        TeamMember, TeamMember.team_id == Team.id
    ).filter(
        TeamMember.user_id == current_user.id,
        Project.deleted_at.is_(None)
    ).limit(10).all()
    
    my_projects = []
    for project, team in my_projects_data:
        issue_count = db.query(Issue).filter(
            Issue.project_id == project.id,
            Issue.deleted_at.is_(None)
        ).count()
        
        my_projects.append({
            "id": project.id,
            "name": project.name,
            "team_name": team.name,
            "issue_count": issue_count
        })
    
    return {
        "my_issues": my_issues,
        "due_soon": due_soon,
        "recent_comments": recent_comments,
        "my_teams": my_teams,
        "my_projects": my_projects
    }


@router.get("/project/{project_id}", response_model=ProjectDashboard)
def get_project_dashboard(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get project dashboard statistics"""
    # Check project access
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    member = db.query(TeamMember).filter(
        TeamMember.team_id == project.team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not member:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Issue stats by status
    issue_stats = {}
    stats_by_status = db.query(Issue.status, func.count(Issue.id)).filter(
        Issue.project_id == project_id,
        Issue.deleted_at.is_(None)
    ).group_by(Issue.status).all()
    
    for status, count in stats_by_status:
        issue_stats[status] = count
    
    # Completion rate
    total_issues = sum(issue_stats.values())
    done_count = issue_stats.get("Done", 0)
    completion_rate = done_count / total_issues if total_issues > 0 else 0.0
    
    # Priority stats
    priority_stats = {}
    stats_by_priority = db.query(Issue.priority, func.count(Issue.id)).filter(
        Issue.project_id == project_id,
        Issue.deleted_at.is_(None)
    ).group_by(Issue.priority).all()
    
    for priority, count in stats_by_priority:
        priority_stats[priority.value] = count
    
    # Recent issues
    recent_issues_data = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.deleted_at.is_(None)
    ).order_by(Issue.created_at.desc()).limit(5).all()
    
    recent_issues = []
    for issue in recent_issues_data:
        recent_issues.append({
            "id": issue.id,
            "title": issue.title,
            "due_date": str(issue.due_date) if issue.due_date else None,
            "project_name": project.name,
            "status": issue.status
        })
    
    # Due soon (within 7 days)
    seven_days_later = datetime.utcnow().date() + timedelta(days=7)
    due_soon_data = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.due_date.isnot(None),
        Issue.due_date <= seven_days_later,
        Issue.deleted_at.is_(None)
    ).order_by(Issue.due_date.asc()).limit(5).all()
    
    due_soon = []
    for issue in due_soon_data:
        due_soon.append({
            "id": issue.id,
            "title": issue.title,
            "due_date": str(issue.due_date),
            "project_name": project.name,
            "status": issue.status
        })
    
    return {
        "issue_stats": issue_stats,
        "completion_rate": completion_rate,
        "priority_stats": priority_stats,
        "recent_issues": recent_issues,
        "due_soon": due_soon
    }
