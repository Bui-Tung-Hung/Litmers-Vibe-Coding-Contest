from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User
from backend.models.issue import Issue, Comment, Label
from backend.models.project import Project
from backend.models.team import TeamMember
from backend.services.ai_service import (
    generate_summary,
    generate_suggestion,
    recommend_labels,
    detect_duplicates,
    summarize_comments,
    check_rate_limit,
)
from backend.dependencies import get_current_user
from pydantic import BaseModel
from datetime import datetime
from typing import List

router = APIRouter()


class AISummaryRequest(BaseModel):
    issue_id: int


class AISuggestionRequest(BaseModel):
    issue_id: int


class AILabelRequest(BaseModel):
    project_id: int
    title: str
    description: str


class AIDuplicateRequest(BaseModel):
    project_id: int
    title: str


class AICommentSummaryRequest(BaseModel):
    issue_id: int


class LabelBrief(BaseModel):
    id: int
    name: str
    color: str


class IssueBrief(BaseModel):
    id: int
    title: str


@router.post("/summary")
async def get_ai_summary(
    request: AISummaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate AI summary for an issue"""
    # Check rate limit
    check_rate_limit(db, current_user.id)
    
    # Get issue
    issue = db.query(Issue).filter(
        Issue.id == request.issue_id,
        Issue.deleted_at.is_(None)
    ).first()
    
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    # Check access
    project = db.query(Project).filter(Project.id == issue.project_id).first()
    member = db.query(TeamMember).filter(
        TeamMember.team_id == project.team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    # Check if cached
    if issue.ai_summary and issue.ai_summary_cached_at:
        return {"summary": issue.ai_summary}
    
    # Generate summary
    summary = await generate_summary(issue.description or "")
    
    # Cache result
    issue.ai_summary = summary
    issue.ai_summary_cached_at = datetime.utcnow()
    db.commit()
    
    return {"summary": summary}


@router.post("/suggestion")
async def get_ai_suggestion(
    request: AISuggestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate AI solution suggestion for an issue"""
    # Check rate limit
    check_rate_limit(db, current_user.id)
    
    # Get issue
    issue = db.query(Issue).filter(
        Issue.id == request.issue_id,
        Issue.deleted_at.is_(None)
    ).first()
    
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    # Check access
    project = db.query(Project).filter(Project.id == issue.project_id).first()
    member = db.query(TeamMember).filter(
        TeamMember.team_id == project.team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    # Check if cached
    if issue.ai_suggestion and issue.ai_suggestion_cached_at:
        return {"suggestion": issue.ai_suggestion}
    
    # Generate suggestion
    suggestion = await generate_suggestion(issue.title, issue.description or "")
    
    # Cache result
    issue.ai_suggestion = suggestion
    issue.ai_suggestion_cached_at = datetime.utcnow()
    db.commit()
    
    return {"suggestion": suggestion}


@router.post("/labels", response_model=dict)
async def get_ai_label_recommendations(
    request: AILabelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI label recommendations"""
    # Check rate limit
    check_rate_limit(db, current_user.id)
    
    # Check project access
    project = db.query(Project).filter(
        Project.id == request.project_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    member = db.query(TeamMember).filter(
        TeamMember.team_id == project.team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get available labels
    labels = db.query(Label).filter(Label.project_id == request.project_id).all()
    available_labels = [{"id": l.id, "name": l.name, "color": l.color} for l in labels]
    
    # Get recommendations
    recommended = await recommend_labels(
        request.title,
        request.description,
        available_labels
    )
    
    return {"recommended_labels": recommended}


@router.post("/duplicates", response_model=dict)
async def detect_duplicate_issues(
    request: AIDuplicateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detect duplicate issues"""
    # Check rate limit
    check_rate_limit(db, current_user.id)
    
    # Check project access
    project = db.query(Project).filter(
        Project.id == request.project_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    member = db.query(TeamMember).filter(
        TeamMember.team_id == project.team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get existing issues
    existing_issues = db.query(Issue).filter(
        Issue.project_id == request.project_id,
        Issue.deleted_at.is_(None)
    ).all()
    
    existing_list = [{"id": i.id, "title": i.title} for i in existing_issues]
    
    # Detect duplicates
    similar = await detect_duplicates(request.title, existing_list)
    
    return {"similar_issues": similar}


@router.post("/comment-summary", response_model=dict)
async def get_comment_summary(
    request: AICommentSummaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Summarize comments on an issue"""
    # Check rate limit
    check_rate_limit(db, current_user.id)
    
    # Get issue
    issue = db.query(Issue).filter(
        Issue.id == request.issue_id,
        Issue.deleted_at.is_(None)
    ).first()
    
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    # Check access
    project = db.query(Project).filter(Project.id == issue.project_id).first()
    member = db.query(TeamMember).filter(
        TeamMember.team_id == project.team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    # Get comments
    comments = db.query(Comment, User).join(
        User, User.id == Comment.user_id
    ).filter(
        Comment.issue_id == request.issue_id,
        Comment.deleted_at.is_(None)
    ).all()
    
    if len(comments) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 5 comments required for summary"
        )
    
    # Format comments
    comment_list = []
    for comment, user in comments:
        comment_list.append({
            "content": comment.content,
            "user": {"name": user.name}
        })
    
    # Generate summary
    summary = await summarize_comments(comment_list)
    
    return {"summary": summary}
