from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.database import get_db
from backend.models.user import User
from backend.models.team import TeamMember
from backend.models.project import Project
from backend.models.issue import Issue, IssueLabel, Label, IssuePriority
from backend.models.activity import IssueHistory
from backend.schemas.issue import (
    IssueCreate,
    IssueUpdate,
    Issue as IssueSchema,
    IssueDetail,
    IssuePositionUpdate,
    UserBrief,
    LabelBrief,
)
from backend.dependencies import get_current_user
from datetime import datetime
from typing import Optional

router = APIRouter()


def check_project_member(db: Session, user_id: int, project_id: int):
    """Check if user is a member of the project's team"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    member = db.query(TeamMember).filter(
        TeamMember.team_id == project.team_id,
        TeamMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project


@router.post("/projects/{project_id}/issues", response_model=IssueSchema, status_code=status.HTTP_201_CREATED)
def create_issue(
    project_id: int,
    issue_data: IssueCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new issue"""
    project = check_project_member(db, current_user.id, project_id)
    
    # Check issue limit
    issue_count = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.deleted_at.is_(None)
    ).count()
    
    if issue_count >= 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has reached maximum issue limit (200)"
        )
    
    # Validate assignee is team member
    if issue_data.assignee_id:
        assignee_member = db.query(TeamMember).filter(
            TeamMember.team_id == project.team_id,
            TeamMember.user_id == issue_data.assignee_id
        ).first()
        if not assignee_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be a team member"
            )
    
    # Get max position for Backlog status
    max_position = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.status == "Backlog",
        Issue.deleted_at.is_(None)
    ).count()
    
    # Create issue
    issue = Issue(
        project_id=project_id,
        title=issue_data.title,
        description=issue_data.description,
        priority=issue_data.priority,
        assignee_id=issue_data.assignee_id,
        owner_id=current_user.id,
        due_date=issue_data.due_date,
        status="Backlog",
        position=max_position
    )
    db.add(issue)
    db.flush()
    
    # Add labels
    if issue_data.label_ids:
        if len(issue_data.label_ids) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 5 labels per issue"
            )
        
        for label_id in issue_data.label_ids:
            issue_label = IssueLabel(issue_id=issue.id, label_id=label_id)
            db.add(issue_label)
    
    db.commit()
    db.refresh(issue)
    
    # Fetch related data for response
    owner = db.query(User).filter(User.id == issue.owner_id).first()
    assignee = db.query(User).filter(User.id == issue.assignee_id).first() if issue.assignee_id else None
    labels = db.query(Label).join(IssueLabel).filter(IssueLabel.issue_id == issue.id).all()
    
    return {
        **issue.__dict__,
        "owner": UserBrief(**owner.__dict__) if owner else None,
        "assignee": UserBrief(**assignee.__dict__) if assignee else None,
        "labels": [LabelBrief(**label.__dict__) for label in labels]
    }


@router.get("/projects/{project_id}/issues", response_model=list[IssueSchema])
def get_issues(
    project_id: int,
    status: Optional[str] = Query(None),
    assignee_id: Optional[int] = Query(None),
    priority: Optional[IssuePriority] = Query(None),
    label_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get issues for a project with filters"""
    check_project_member(db, current_user.id, project_id)
    
    query = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.deleted_at.is_(None)
    )
    
    # Apply filters
    if status:
        query = query.filter(Issue.status == status)
    if assignee_id:
        query = query.filter(Issue.assignee_id == assignee_id)
    if priority:
        query = query.filter(Issue.priority == priority)
    if label_id:
        query = query.join(IssueLabel).filter(IssueLabel.label_id == label_id)
    if search:
        query = query.filter(Issue.title.ilike(f"%{search}%"))
    
    issues = query.order_by(Issue.position.asc()).all()
    
    result = []
    for issue in issues:
        owner = db.query(User).filter(User.id == issue.owner_id).first()
        assignee = db.query(User).filter(User.id == issue.assignee_id).first() if issue.assignee_id else None
        labels = db.query(Label).join(IssueLabel).filter(IssueLabel.issue_id == issue.id).all()
        
        result.append({
            **issue.__dict__,
            "owner": UserBrief(**owner.__dict__) if owner else None,
            "assignee": UserBrief(**assignee.__dict__) if assignee else None,
            "labels": [LabelBrief(**label.__dict__) for label in labels]
        })
    
    return result


@router.get("/issues/{issue_id}", response_model=IssueDetail)
def get_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get issue details"""
    issue = db.query(Issue).filter(
        Issue.id == issue_id,
        Issue.deleted_at.is_(None)
    ).first()
    
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    # Check access
    check_project_member(db, current_user.id, issue.project_id)
    
    # Fetch related data
    owner = db.query(User).filter(User.id == issue.owner_id).first()
    assignee = db.query(User).filter(User.id == issue.assignee_id).first() if issue.assignee_id else None
    labels = db.query(Label).join(IssueLabel).filter(IssueLabel.issue_id == issue.id).all()
    
    from backend.models.issue import Comment
    comment_count = db.query(Comment).filter(
        Comment.issue_id == issue_id,
        Comment.deleted_at.is_(None)
    ).count()
    
    return {
        **issue.__dict__,
        "owner": UserBrief(**owner.__dict__) if owner else None,
        "assignee": UserBrief(**assignee.__dict__) if assignee else None,
        "labels": [LabelBrief(**label.__dict__) for label in labels],
        "comment_count": comment_count
    }


@router.put("/issues/{issue_id}", response_model=IssueSchema)
def update_issue(
    issue_id: int,
    issue_data: IssueUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update issue"""
    issue = db.query(Issue).filter(
        Issue.id == issue_id,
        Issue.deleted_at.is_(None)
    ).first()
    
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    project = check_project_member(db, current_user.id, issue.project_id)
    
    # Save old values for history tracking
    old_title = issue.title
    old_status = issue.status
    old_priority = issue.priority
    old_assignee_id = issue.assignee_id
    old_due_date = issue.due_date
    
    # Track changes
    changes = []
    
    # Update fields
    if issue_data.title is not None and issue_data.title != old_title:
        issue.title = issue_data.title
        changes.append(("title", str(old_title), str(issue_data.title)))
    if issue_data.description is not None:
        issue.description = issue_data.description
        # Invalidate AI cache when description changes
        issue.ai_summary = None
        issue.ai_summary_cached_at = None
        issue.ai_suggestion = None
        issue.ai_suggestion_cached_at = None
    if issue_data.priority is not None and issue_data.priority != old_priority:
        issue.priority = issue_data.priority
        changes.append(("priority", old_priority.value if old_priority else None, issue_data.priority.value))
    if issue_data.assignee_id is not None and issue_data.assignee_id != old_assignee_id:
        # Validate assignee
        if issue_data.assignee_id:
            assignee_member = db.query(TeamMember).filter(
                TeamMember.team_id == project.team_id,
                TeamMember.user_id == issue_data.assignee_id
            ).first()
            if not assignee_member:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignee must be a team member"
                )
        issue.assignee_id = issue_data.assignee_id
        
        # Track assignee change
        old_assignee_name = None
        new_assignee_name = None
        if old_assignee_id:
            old_assignee = db.query(User).filter(User.id == old_assignee_id).first()
            old_assignee_name = old_assignee.name if old_assignee else None
        if issue_data.assignee_id:
            new_assignee = db.query(User).filter(User.id == issue_data.assignee_id).first()
            new_assignee_name = new_assignee.name if new_assignee else None
        changes.append(("assignee", old_assignee_name, new_assignee_name))
        
    if issue_data.due_date is not None and issue_data.due_date != old_due_date:
        issue.due_date = issue_data.due_date
        changes.append(("due_date", str(old_due_date) if old_due_date else None, str(issue_data.due_date) if issue_data.due_date else None))
    if issue_data.status is not None and issue_data.status != old_status:
        issue.status = issue_data.status
        changes.append(("status", str(old_status), str(issue_data.status)))
    
    # Update labels
    if issue_data.label_ids is not None:
        if len(issue_data.label_ids) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 5 labels per issue"
            )
        # Remove old labels
        db.query(IssueLabel).filter(IssueLabel.issue_id == issue_id).delete()
        # Add new labels
        for label_id in issue_data.label_ids:
            issue_label = IssueLabel(issue_id=issue_id, label_id=label_id)
            db.add(issue_label)
    
    issue.updated_at = datetime.utcnow()
    db.commit()
    
    # Create history entries for all changes
    for field, old_value, new_value in changes:
        history = IssueHistory(
            issue_id=issue_id,
            user_id=current_user.id,
            field=field,
            old_value=old_value,
            new_value=new_value
        )
        db.add(history)
    
    db.commit()
    db.refresh(issue)
    
    # Fetch related data
    owner = db.query(User).filter(User.id == issue.owner_id).first()
    assignee = db.query(User).filter(User.id == issue.assignee_id).first() if issue.assignee_id else None
    labels = db.query(Label).join(IssueLabel).filter(IssueLabel.issue_id == issue.id).all()
    
    return {
        **issue.__dict__,
        "owner": UserBrief(**owner.__dict__) if owner else None,
        "assignee": UserBrief(**assignee.__dict__) if assignee else None,
        "labels": [LabelBrief(**label.__dict__) for label in labels]
    }


@router.delete("/issues/{issue_id}")
def delete_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete issue (owner, project owner, or team admin/owner)"""
    from backend.models.team import TeamRole
    
    issue = db.query(Issue).filter(
        Issue.id == issue_id,
        Issue.deleted_at.is_(None)
    ).first()
    
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    project = db.query(Project).filter(Project.id == issue.project_id).first()
    
    # Check permissions
    member = db.query(TeamMember).filter(
        TeamMember.team_id == project.team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    # Can delete if: issue owner, project owner, or team OWNER/ADMIN
    if (issue.owner_id != current_user.id and 
        project.owner_id != current_user.id and
        member.role not in [TeamRole.OWNER, TeamRole.ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    issue.deleted_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Issue deleted successfully"}


@router.get("/issues/{issue_id}/history")
def get_issue_history(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get issue change history"""
    issue = db.query(Issue).filter(
        Issue.id == issue_id,
        Issue.deleted_at.is_(None)
    ).first()
    
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    # Check access
    check_project_member(db, current_user.id, issue.project_id)
    
    # Get history with user info
    histories = db.query(IssueHistory, User).join(
        User, User.id == IssueHistory.user_id
    ).filter(
        IssueHistory.issue_id == issue_id
    ).order_by(
        IssueHistory.created_at.desc()
    ).all()
    
    result = []
    for history, user in histories:
        result.append({
            "id": history.id,
            "field": history.field,
            "old_value": history.old_value,
            "new_value": history.new_value,
            "created_at": history.created_at,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "profile_image": user.profile_image
            }
        })
    
    return result


@router.put("/issues/{issue_id}/position", response_model=IssueSchema)
def update_issue_position(
    issue_id: int,
    position_data: IssuePositionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update issue position and status (for drag & drop)"""
    issue = db.query(Issue).filter(
        Issue.id == issue_id,
        Issue.deleted_at.is_(None)
    ).first()
    
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    check_project_member(db, current_user.id, issue.project_id)
    
    old_status = issue.status
    new_status = position_data.status
    
    # Update status and position
    issue.status = new_status
    issue.position = position_data.position
    issue.updated_at = datetime.utcnow()
    
    # Reorder other issues in the same status
    if old_status != new_status:
        # Reorder issues in old status
        db.query(Issue).filter(
            Issue.project_id == issue.project_id,
            Issue.status == old_status,
            Issue.position > issue.position,
            Issue.deleted_at.is_(None)
        ).update({"position": Issue.position - 1})
    
    db.commit()
    db.refresh(issue)
    
    # Fetch related data
    owner = db.query(User).filter(User.id == issue.owner_id).first()
    assignee = db.query(User).filter(User.id == issue.assignee_id).first() if issue.assignee_id else None
    labels = db.query(Label).join(IssueLabel).filter(IssueLabel.issue_id == issue.id).all()
    
    return {
        **issue.__dict__,
        "owner": UserBrief(**owner.__dict__) if owner else None,
        "assignee": UserBrief(**assignee.__dict__) if assignee else None,
        "labels": [LabelBrief(**label.__dict__) for label in labels]
    }
