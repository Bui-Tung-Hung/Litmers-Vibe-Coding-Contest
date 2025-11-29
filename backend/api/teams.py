from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend.models.user import User
from backend.models.team import Team, TeamMember, TeamInvite, TeamRole, InviteStatus
from backend.models.project import Project
from backend.models.activity import TeamActivityLog
from backend.schemas.team import (
    TeamCreate,
    TeamUpdate,
    Team as TeamSchema,
    TeamWithRole,
    TeamMember as TeamMemberSchema,
    TeamInviteCreate,
    RoleChange,
)
from backend.dependencies import get_current_user
from backend.services.email_service import send_invite_email
from backend.services.activity_logger import (
    log_member_joined,
    log_member_removed,
    log_role_changed,
    log_team_updated
)
from datetime import datetime, timedelta
import asyncio

router = APIRouter()


def get_user_role_in_team(db: Session, user_id: int, team_id: int) -> TeamRole:
    """Get user's role in a team"""
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    ).first()
    return member.role if member else None


def check_team_permission(db: Session, user_id: int, team_id: int, required_roles: list):
    """Check if user has required permission in team"""
    role = get_user_role_in_team(db, user_id, team_id)
    if role not in required_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return role


@router.post("", response_model=TeamSchema, status_code=status.HTTP_201_CREATED)
def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new team"""
    # Create team
    team = Team(
        name=team_data.name,
        owner_id=current_user.id
    )
    db.add(team)
    db.flush()
    
    # Add creator as OWNER member
    member = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role=TeamRole.OWNER
    )
    db.add(member)
    db.commit()
    db.refresh(team)
    
    return team


@router.get("", response_model=list[TeamWithRole])
def get_teams(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all teams user belongs to"""
    teams = db.query(Team, TeamMember.role).join(
        TeamMember, TeamMember.team_id == Team.id
    ).filter(
        TeamMember.user_id == current_user.id,
        Team.deleted_at.is_(None)
    ).all()
    
    result = []
    for team, role in teams:
        member_count = db.query(TeamMember).filter(
            TeamMember.team_id == team.id
        ).count()
        
        project_count = db.query(Project).filter(
            Project.team_id == team.id,
            Project.deleted_at.is_(None)
        ).count()
        
        result.append({
            **team.__dict__,
            "my_role": role,
            "member_count": member_count,
            "project_count": project_count
        })
    
    return result


@router.get("/{team_id}", response_model=TeamSchema)
def get_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get team details"""
    role = get_user_role_in_team(db, current_user.id, team_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    team = db.query(Team).filter(
        Team.id == team_id,
        Team.deleted_at.is_(None)
    ).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    return team


@router.put("/{team_id}", response_model=TeamSchema)
def update_team(
    team_id: int,
    team_data: TeamUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update team (OWNER, ADMIN only)"""
    check_team_permission(db, current_user.id, team_id, [TeamRole.OWNER, TeamRole.ADMIN])
    
    team = db.query(Team).filter(
        Team.id == team_id,
        Team.deleted_at.is_(None)
    ).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    old_name = team.name
    team.name = team_data.name
    db.commit()
    db.refresh(team)
    
    # Log activity if name changed
    if old_name != team_data.name:
        log_team_updated(db, team_id, current_user.id, old_name, team_data.name)
    
    return team


@router.delete("/{team_id}")
def delete_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete team (OWNER only)"""
    check_team_permission(db, current_user.id, team_id, [TeamRole.OWNER])
    
    team = db.query(Team).filter(
        Team.id == team_id,
        Team.deleted_at.is_(None)
    ).first()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Soft delete team and related data
    team.deleted_at = datetime.utcnow()
    
    # Soft delete projects
    projects = db.query(Project).filter(Project.team_id == team_id).all()
    for project in projects:
        project.deleted_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Team deleted successfully"}


@router.get("/{team_id}/members", response_model=list[TeamMemberSchema])
def get_team_members(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get team members"""
    role = get_user_role_in_team(db, current_user.id, team_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    members = db.query(TeamMember, User).join(
        User, User.id == TeamMember.user_id
    ).filter(
        TeamMember.team_id == team_id,
        User.deleted_at.is_(None)
    ).all()
    
    result = []
    for member, user in members:
        result.append({
            "id": member.id,
            "team_id": member.team_id,
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "profile_image": user.profile_image,
            "role": member.role,
            "joined_at": member.joined_at
        })
    
    return result


@router.post("/{team_id}/invite", status_code=status.HTTP_201_CREATED)
async def invite_member(
    team_id: int,
    invite_data: TeamInviteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invite member to team (OWNER, ADMIN only)"""
    check_team_permission(db, current_user.id, team_id, [TeamRole.OWNER, TeamRole.ADMIN])
    
    # Get team info
    team = db.query(Team).filter(Team.id == team_id).first()
    
    # Check if user is already a member
    existing_user = db.query(User).filter(User.email == invite_data.email).first()
    if existing_user:
        existing_member = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == existing_user.id
        ).first()
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a team member"
            )
    
    # Check for existing pending invite
    existing_invite = db.query(TeamInvite).filter(
        TeamInvite.team_id == team_id,
        TeamInvite.email == invite_data.email,
        TeamInvite.status == InviteStatus.PENDING
    ).first()
    
    if existing_invite:
        # Update expiration date
        existing_invite.expires_at = datetime.utcnow() + timedelta(days=7)
        db.commit()
        
        # Resend email
        try:
            await send_invite_email(invite_data.email, team.name, current_user.name)
        except Exception as e:
            print(f"Failed to send email: {e}")
        
        return {"message": "Invitation resent successfully"}
    
    # Create invite
    invite = TeamInvite(
        team_id=team_id,
        email=invite_data.email,
        invited_by=current_user.id,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(invite)
    db.commit()
    
    # Send email
    try:
        await send_invite_email(invite_data.email, team.name, current_user.name)
    except Exception as e:
        print(f"Failed to send email: {e}")
        # Don't fail the request if email fails
    
    return {"message": "Invitation sent successfully"}


@router.put("/{team_id}/members/{user_id}/role")
def change_member_role(
    team_id: int,
    user_id: int,
    role_data: RoleChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change member role (OWNER only)"""
    check_team_permission(db, current_user.id, team_id, [TeamRole.OWNER])
    
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Cannot change own role
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    # Get user info for logging
    target_user = db.query(User).filter(User.id == user_id).first()
    old_role = member.role
    
    member.role = role_data.role
    db.commit()
    
    # Log activity
    log_role_changed(db, team_id, current_user.id, user_id, target_user.name, old_role.value, role_data.role.value)
    
    return {"message": "Role updated successfully"}


@router.delete("/{team_id}/members/{user_id}")
def kick_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kick member from team"""
    user_role = get_user_role_in_team(db, current_user.id, team_id)
    target_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    ).first()
    
    if not target_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # OWNER can kick anyone, ADMIN can only kick MEMBER
    if user_role == TeamRole.OWNER:
        pass
    elif user_role == TeamRole.ADMIN and target_member.role == TeamRole.MEMBER:
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Cannot kick self
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot kick yourself. Use leave endpoint instead."
        )
    
    # Get user info for logging
    target_user = db.query(User).filter(User.id == user_id).first()
    
    db.delete(target_member)
    db.commit()
    
    # Log activity
    log_member_removed(db, team_id, current_user.id, user_id, target_user.name, was_kicked=True)
    
    return {"message": "Member removed successfully"}


@router.post("/{team_id}/leave")
def leave_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Leave team (ADMIN, MEMBER only)"""
    role = get_user_role_in_team(db, current_user.id, team_id)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    if role == TeamRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner cannot leave team. Delete the team or transfer ownership first."
        )
    
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    db.delete(member)
    db.commit()
    
    # Log activity
    log_member_removed(db, team_id, current_user.id, current_user.id, current_user.name, was_kicked=False)
    
    return {"message": "Left team successfully"}


@router.get("/{team_id}/activity")
def get_team_activity(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0
):
    """Get team activity log with pagination"""
    # Check team access
    role = get_user_role_in_team(db, current_user.id, team_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Get activities with user info
    activities = db.query(TeamActivityLog, User).join(
        User, User.id == TeamActivityLog.user_id
    ).filter(
        TeamActivityLog.team_id == team_id
    ).order_by(
        TeamActivityLog.created_at.desc()
    ).limit(limit).offset(offset).all()
    
    result = []
    for activity, user in activities:
        result.append({
            "id": activity.id,
            "action": activity.action,
            "target_type": activity.target_type,
            "target_id": activity.target_id,
            "target_name": activity.target_name,
            "details": activity.details,
            "created_at": activity.created_at,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "profile_image": user.profile_image
            }
        })
    
    return result

