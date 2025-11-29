from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User
from backend.schemas.user import User as UserSchema, UserUpdate, PasswordChange
from backend.dependencies import get_current_user
from backend.services.auth_service import get_password_hash, verify_password

router = APIRouter()


@router.get("/me", response_model=UserSchema)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@router.put("/me", response_model=UserSchema)
def update_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    if user_data.name is not None:
        current_user.name = user_data.name
    
    if user_data.profile_image is not None:
        current_user.profile_image = user_data.profile_image
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.put("/me/password")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    # Check if user has password (not Google OAuth only)
    if not current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password change not available for Google OAuth users"
        )
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.delete("/me")
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user account (soft delete)"""
    from backend.models.team import Team
    from datetime import datetime
    
    # Check if user owns any teams
    owned_teams = db.query(Team).filter(
        Team.owner_id == current_user.id,
        Team.deleted_at.is_(None)
    ).first()
    
    if owned_teams:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please delete owned teams or transfer ownership first"
        )
    
    # Soft delete user
    current_user.deleted_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Account deleted successfully"}
