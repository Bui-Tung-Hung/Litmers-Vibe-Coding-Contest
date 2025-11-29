from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend.models.user import User
from backend.models.team import TeamMember, TeamRole
from backend.models.project import Project, ProjectFavorite
from backend.models.issue import Issue, Label
from backend.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    Project as ProjectSchema,
    ProjectDetail,
    ArchiveProject,
    LabelCreate,
    Label as LabelSchema,
)
from backend.dependencies import get_current_user
from backend.services.activity_logger import (
    log_project_created,
    log_project_archived,
    log_project_deleted
)
from datetime import datetime

router = APIRouter()


def get_user_role_in_team(db: Session, user_id: int, team_id: int):
    """Get user's role in a team"""
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    ).first()
    return member.role if member else None


def check_project_access(db: Session, user_id: int, project_id: int):
    """Check if user has access to project"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    role = get_user_role_in_team(db, user_id, project.team_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project, role


@router.post("/teams/{team_id}/projects", response_model=ProjectSchema, status_code=status.HTTP_201_CREATED)
def create_project(
    team_id: int,
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new project"""
    # Check team membership
    role = get_user_role_in_team(db, current_user.id, team_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Check project limit
    project_count = db.query(Project).filter(
        Project.team_id == team_id,
        Project.deleted_at.is_(None)
    ).count()
    
    if project_count >= 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team has reached maximum project limit (15)"
        )
    
    # Create project
    project = Project(
        team_id=team_id,
        name=project_data.name,
        description=project_data.description,
        owner_id=current_user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Log activity
    log_project_created(db, team_id, current_user.id, project.id, project.name)
    
    # Add additional fields for response
    project.is_favorite = False
    project.issue_count = 0
    
    return project


@router.get("/teams/{team_id}/projects", response_model=list[ProjectSchema])
def get_team_projects(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all projects in a team"""
    # Check team membership
    role = get_user_role_in_team(db, current_user.id, team_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    projects = db.query(Project).filter(
        Project.team_id == team_id,
        Project.deleted_at.is_(None)
    ).all()
    
    result = []
    for project in projects:
        # Check if favorited by current user
        is_favorite = db.query(ProjectFavorite).filter(
            ProjectFavorite.project_id == project.id,
            ProjectFavorite.user_id == current_user.id
        ).first() is not None
        
        # Get issue count
        issue_count = db.query(Issue).filter(
            Issue.project_id == project.id,
            Issue.deleted_at.is_(None)
        ).count()
        
        result.append({
            **project.__dict__,
            "is_favorite": is_favorite,
            "issue_count": issue_count
        })
    
    # Sort: favorites first, then by created_at desc
    result.sort(key=lambda x: (not x["is_favorite"], -x["created_at"].timestamp()))
    
    return result


@router.get("/projects/{project_id}", response_model=ProjectDetail)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get project details with statistics"""
    project, role = check_project_access(db, current_user.id, project_id)
    
    # Check if favorited
    is_favorite = db.query(ProjectFavorite).filter(
        ProjectFavorite.project_id == project_id,
        ProjectFavorite.user_id == current_user.id
    ).first() is not None
    
    # Get issue statistics by status
    issue_stats = {}
    issues = db.query(Issue.status, func.count(Issue.id)).filter(
        Issue.project_id == project_id,
        Issue.deleted_at.is_(None)
    ).group_by(Issue.status).all()
    
    for status, count in issues:
        issue_stats[status] = count
    
    total_issues = sum(issue_stats.values())
    
    return {
        **project.__dict__,
        "is_favorite": is_favorite,
        "issue_count": total_issues,
        "issue_stats": issue_stats
    }


@router.put("/projects/{project_id}", response_model=ProjectSchema)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update project (OWNER, ADMIN, or project owner)"""
    project, role = check_project_access(db, current_user.id, project_id)
    
    # Check permissions
    if role not in [TeamRole.OWNER, TeamRole.ADMIN] and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    
    db.commit()
    db.refresh(project)
    
    # Add extra fields
    is_favorite = db.query(ProjectFavorite).filter(
        ProjectFavorite.project_id == project_id,
        ProjectFavorite.user_id == current_user.id
    ).first() is not None
    
    issue_count = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.deleted_at.is_(None)
    ).count()
    
    project.is_favorite = is_favorite
    project.issue_count = issue_count
    
    return project


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete project (OWNER, ADMIN, or project owner)"""
    project, role = check_project_access(db, current_user.id, project_id)
    
    # Check permissions
    if role not in [TeamRole.OWNER, TeamRole.ADMIN] and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Soft delete project and issues
    project.deleted_at = datetime.utcnow()
    
    issues = db.query(Issue).filter(Issue.project_id == project_id).all()
    for issue in issues:
        issue.deleted_at = datetime.utcnow()
    
    db.commit()
    
    # Log activity
    log_project_deleted(db, project.team_id, current_user.id, project_id, project.name)
    
    return {"message": "Project deleted successfully"}


@router.post("/projects/{project_id}/favorite")
def favorite_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add project to favorites"""
    project, role = check_project_access(db, current_user.id, project_id)
    
    # Check if already favorited
    existing = db.query(ProjectFavorite).filter(
        ProjectFavorite.project_id == project_id,
        ProjectFavorite.user_id == current_user.id
    ).first()
    
    if existing:
        return {"is_favorite": True}
    
    favorite = ProjectFavorite(
        project_id=project_id,
        user_id=current_user.id
    )
    db.add(favorite)
    db.commit()
    
    return {"is_favorite": True}


@router.delete("/projects/{project_id}/favorite")
def unfavorite_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove project from favorites"""
    project, role = check_project_access(db, current_user.id, project_id)
    
    favorite = db.query(ProjectFavorite).filter(
        ProjectFavorite.project_id == project_id,
        ProjectFavorite.user_id == current_user.id
    ).first()
    
    if favorite:
        db.delete(favorite)
        db.commit()
    
    return {"is_favorite": False}


@router.put("/projects/{project_id}/archive", response_model=ProjectSchema)
def archive_project(
    project_id: int,
    archive_data: ArchiveProject,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Archive or restore project"""
    project, role = check_project_access(db, current_user.id, project_id)
    
    # Check permissions
    if role not in [TeamRole.OWNER, TeamRole.ADMIN] and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    project.is_archived = archive_data.is_archived
    db.commit()
    db.refresh(project)
    
    # Log activity
    log_project_archived(db, project.team_id, current_user.id, project_id, project.name, archive_data.is_archived)
    
    # Add extra fields
    is_favorite = db.query(ProjectFavorite).filter(
        ProjectFavorite.project_id == project_id,
        ProjectFavorite.user_id == current_user.id
    ).first() is not None
    
    issue_count = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.deleted_at.is_(None)
    ).count()
    
    project.is_favorite = is_favorite
    project.issue_count = issue_count
    
    return project


# Label endpoints
@router.post("/projects/{project_id}/labels", response_model=LabelSchema, status_code=status.HTTP_201_CREATED)
def create_label(
    project_id: int,
    label_data: LabelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a label for project"""
    project, role = check_project_access(db, current_user.id, project_id)
    
    # Check label limit
    label_count = db.query(Label).filter(Label.project_id == project_id).count()
    if label_count >= 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has reached maximum label limit (20)"
        )
    
    # Check for duplicate name
    existing = db.query(Label).filter(
        Label.project_id == project_id,
        Label.name == label_data.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Label with this name already exists"
        )
    
    label = Label(
        project_id=project_id,
        name=label_data.name,
        color=label_data.color
    )
    db.add(label)
    db.commit()
    db.refresh(label)
    
    return label


@router.get("/projects/{project_id}/labels", response_model=list[LabelSchema])
def get_labels(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all labels for a project"""
    project, role = check_project_access(db, current_user.id, project_id)
    
    labels = db.query(Label).filter(Label.project_id == project_id).all()
    return labels


@router.delete("/labels/{label_id}")
def delete_label(
    label_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a label"""
    label = db.query(Label).filter(Label.id == label_id).first()
    
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label not found"
        )
    
    # Check access to project
    project, role = check_project_access(db, current_user.id, label.project_id)
    
    db.delete(label)
    db.commit()
    
    return {"message": "Label deleted successfully"}
