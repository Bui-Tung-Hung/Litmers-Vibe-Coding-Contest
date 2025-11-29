from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./litmer.db"
    
    # JWT
    secret_key: str = "default-secret-key-change-me"
    algorithm: str = "HS256"
    access_token_expire_hours: int = 24
    
    # Google OAuth - Read from os.environ as fallback for Railway
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5173/auth/google/callback")
    google_auth_uri: str = "https://accounts.google.com/o/oauth2/v2/auth"
    google_token_uri: str = "https://oauth2.googleapis.com/token"
    google_userinfo_uri: str = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = ""
    
    # Gemini AI
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    
    # CORS
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    class Config:
        env_file = str(Path(__file__).parent / ".env")
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()
