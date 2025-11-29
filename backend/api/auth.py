from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User, PasswordResetToken
from backend.schemas.user import (
    UserCreate,
    UserLogin,
    Token,
    ForgotPassword,
    ResetPassword,
)
from backend.services.auth_service import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from backend.services.email_service import send_password_reset_email
from backend.config import get_settings
from datetime import datetime, timedelta
import secrets
import httpx
from urllib.parse import urlencode

settings = get_settings()
router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with email/password"""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    db_user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password),
        auth_provider="email"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create access token
    access_token = create_access_token(data={"sub": str(db_user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user
    }


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login with email/password"""
    user = db.query(User).filter(
        User.email == credentials.email,
        User.deleted_at.is_(None)
    ).first()
    
    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect"
        )
    
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/forgot-password")
async def forgot_password(data: ForgotPassword, db: Session = Depends(get_db)):
    """Request password reset"""
    user = db.query(User).filter(
        User.email == data.email,
        User.deleted_at.is_(None),
        User.auth_provider == "email"
    ).first()
    
    if not user:
        # Don't reveal if email exists
        return {"message": "Password reset email sent"}
    
    # Generate reset token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )
    db.add(reset_token)
    db.commit()
    
    # Send email with reset link
    try:
        await send_password_reset_email(user.email, token, user.name)
    except Exception as e:
        print(f"Failed to send password reset email: {e}")
        # Don't fail the request if email fails
    
    return {"message": "Password reset email sent"}


@router.post("/reset-password")
def reset_password(data: ResetPassword, db: Session = Depends(get_db)):
    """Reset password using token"""
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == data.token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update password
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    user.password_hash = get_password_hash(data.new_password)
    
    # Mark token as used
    reset_token.used = True
    
    db.commit()
    
    return {"message": "Password reset successful"}


@router.get("/google/login")
def google_login():
    """Redirect to Google OAuth login"""
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    auth_url = f"{settings.google_auth_uri}?{urlencode(params)}"
    return {"auth_url": auth_url}


@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided"
        )
    
    # Exchange code for token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            settings.google_token_uri,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code"
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code"
            )
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        # Get user info from Google
        userinfo_response = await client.get(
            settings.google_userinfo_uri,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info"
            )
        
        user_info = userinfo_response.json()
        email = user_info.get("email")
        name = user_info.get("name", email.split("@")[0])
        google_id = user_info.get("id")
        
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            # Update existing user
            if not user.google_id:
                user.google_id = google_id
                user.auth_provider = "google"
        else:
            # Create new user
            user = User(
                email=email,
                name=name,
                google_id=google_id,
                auth_provider="google",
                password_hash=None  # No password for OAuth users
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)
        
        # Create JWT token
        jwt_token = create_access_token(data={"sub": str(user.id)})
        
        # Redirect to frontend with token
        frontend_url = f"{settings.frontend_url}/auth/google/callback?token={jwt_token}"
        return RedirectResponse(url=frontend_url)
