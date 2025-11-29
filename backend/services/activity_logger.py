from sqlalchemy.orm import Session
from backend.models.activity import TeamActivityLog
import json


def log_activity(
    db: Session,
    team_id: int,
    user_id: int,
    action: str,
    target_type: str = None,
    target_id: int = None,
    target_name: str = None,
    details: dict = None
):
    """Base function to log team activity"""
    activity = TeamActivityLog(
        team_id=team_id,
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        target_name=target_name,
        details=json.dumps(details) if details else None
    )
    db.add(activity)
    db.commit()
    return activity


def log_member_joined(db: Session, team_id: int, user_id: int, new_member_id: int, new_member_name: str):
    """Log when a member joins a team"""
    return log_activity(
        db=db,
        team_id=team_id,
        user_id=user_id,
        action="MEMBER_JOINED",
        target_type="USER",
        target_id=new_member_id,
        target_name=new_member_name
    )


def log_member_removed(db: Session, team_id: int, user_id: int, removed_member_id: int, removed_member_name: str, was_kicked: bool = False):
    """Log when a member leaves or is kicked from a team"""
    return log_activity(
        db=db,
        team_id=team_id,
        user_id=user_id,
        action="MEMBER_KICKED" if was_kicked else "MEMBER_LEFT",
        target_type="USER",
        target_id=removed_member_id,
        target_name=removed_member_name
    )


def log_role_changed(db: Session, team_id: int, user_id: int, target_member_id: int, target_member_name: str, old_role: str, new_role: str):
    """Log when a member's role is changed"""
    return log_activity(
        db=db,
        team_id=team_id,
        user_id=user_id,
        action="ROLE_CHANGED",
        target_type="USER",
        target_id=target_member_id,
        target_name=target_member_name,
        details={"old_role": old_role, "new_role": new_role}
    )


def log_project_created(db: Session, team_id: int, user_id: int, project_id: int, project_name: str):
    """Log when a project is created"""
    return log_activity(
        db=db,
        team_id=team_id,
        user_id=user_id,
        action="PROJECT_CREATED",
        target_type="PROJECT",
        target_id=project_id,
        target_name=project_name
    )


def log_project_archived(db: Session, team_id: int, user_id: int, project_id: int, project_name: str, is_archived: bool):
    """Log when a project is archived or restored"""
    return log_activity(
        db=db,
        team_id=team_id,
        user_id=user_id,
        action="PROJECT_ARCHIVED" if is_archived else "PROJECT_RESTORED",
        target_type="PROJECT",
        target_id=project_id,
        target_name=project_name
    )


def log_project_deleted(db: Session, team_id: int, user_id: int, project_id: int, project_name: str):
    """Log when a project is deleted"""
    return log_activity(
        db=db,
        team_id=team_id,
        user_id=user_id,
        action="PROJECT_DELETED",
        target_type="PROJECT",
        target_id=project_id,
        target_name=project_name
    )


def log_team_updated(db: Session, team_id: int, user_id: int, old_name: str, new_name: str):
    """Log when team information is updated"""
    return log_activity(
        db=db,
        team_id=team_id,
        user_id=user_id,
        action="TEAM_UPDATED",
        target_type="TEAM",
        target_id=team_id,
        target_name=new_name,
        details={"old_name": old_name, "new_name": new_name}
    )
