from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User
from backend.models.team import TeamMember, TeamRole
from backend.models.project import Project
from backend.models.issue import Issue, Comment
from backend.schemas.issue import (
    CommentCreate,
    CommentUpdate,
    Comment as CommentSchema,
    UserBrief,
)
from backend.dependencies import get_current_user
from datetime import datetime

router = APIRouter()


def check_issue_access(db: Session, user_id: int, issue_id: int):
    """Check if user has access to issue"""
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
    member = db.query(TeamMember).filter(
        TeamMember.team_id == project.team_id,
        TeamMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    return issue, project, member


@router.post("/issues/{issue_id}/comments", response_model=CommentSchema, status_code=status.HTTP_201_CREATED)
def create_comment(
    issue_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a comment on an issue"""
    issue, project, member = check_issue_access(db, current_user.id, issue_id)
    
    # Validate content length
    if len(comment_data.content) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment content must be 1000 characters or less"
        )
    
    comment = Comment(
        issue_id=issue_id,
        user_id=current_user.id,
        content=comment_data.content
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    # Fetch user data
    user = db.query(User).filter(User.id == comment.user_id).first()
    
    # Create notification for issue owner and assignee
    # TODO: Implement notification service
    
    return {
        **comment.__dict__,
        "user": UserBrief(**user.__dict__)
    }


@router.get("/issues/{issue_id}/comments", response_model=list[CommentSchema])
def get_comments(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all comments for an issue"""
    check_issue_access(db, current_user.id, issue_id)
    
    comments = db.query(Comment).filter(
        Comment.issue_id == issue_id,
        Comment.deleted_at.is_(None)
    ).order_by(Comment.created_at.asc()).all()
    
    result = []
    for comment in comments:
        user = db.query(User).filter(User.id == comment.user_id).first()
        result.append({
            **comment.__dict__,
            "user": UserBrief(**user.__dict__)
        })
    
    return result


@router.put("/comments/{comment_id}", response_model=CommentSchema)
def update_comment(
    comment_id: int,
    comment_data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a comment (author only)"""
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.deleted_at.is_(None)
    ).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Check if user is the author
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments"
        )
    
    # Validate content length
    if len(comment_data.content) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment content must be 1000 characters or less"
        )
    
    comment.content = comment_data.content
    comment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(comment)
    
    user = db.query(User).filter(User.id == comment.user_id).first()
    
    return {
        **comment.__dict__,
        "user": UserBrief(**user.__dict__)
    }


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a comment (author, issue owner, project owner, or team admin/owner)"""
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.deleted_at.is_(None)
    ).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    issue = db.query(Issue).filter(Issue.id == comment.issue_id).first()
    project = db.query(Project).filter(Project.id == issue.project_id).first()
    member = db.query(TeamMember).filter(
        TeamMember.team_id == project.team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    # Can delete if: comment author, issue owner, project owner, or team OWNER/ADMIN
    if (comment.user_id != current_user.id and
        issue.owner_id != current_user.id and
        project.owner_id != current_user.id and
        (not member or member.role not in [TeamRole.OWNER, TeamRole.ADMIN])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    comment.deleted_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Comment deleted successfully"}
