from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
import os

def get_env(key: str, default: str = "") -> str:
    """Get environment variable and strip quotes if present"""
    value = os.getenv(key, default)
    # Strip quotes that Railway might add
    if value and len(value) >= 2:
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
    return value

class Settings(BaseSettings):
    # Database
    database_url: str = get_env("DATABASE_URL", "sqlite:///./litmer.db")
    
    # JWT
    secret_key: str = get_env("SECRET_KEY", "default-secret-key-change-me")
    algorithm: str = get_env("ALGORITHM", "HS256")
    access_token_expire_hours: int = int(get_env("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
    
    # Google OAuth - Strip quotes from Railway
    google_client_id: str = get_env("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = get_env("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = get_env("GOOGLE_REDIRECT_URI", "http://localhost:5173/auth/google/callback")
    google_auth_uri: str = "https://accounts.google.com/o/oauth2/v2/auth"
    google_token_uri: str = "https://oauth2.googleapis.com/token"
    google_userinfo_uri: str = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    # Email
    smtp_host: str = get_env("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(get_env("SMTP_PORT", "587"))
    smtp_user: str = get_env("SMTP_USER", "")
    smtp_password: str = get_env("SMTP_PASSWORD", "")
    from_email: str = get_env("FROM_EMAIL", "")
    
    # Gemini AI
    gemini_api_key: str = get_env("GEMINI_API_KEY", "")
    gemini_model: str = get_env("GEMINI_MODEL", "gemini-2.5-flash")
    
    # CORS
    frontend_url: str = get_env("FRONTEND_URL", "http://localhost:5173")
    
    class Config:
        env_file = str(Path(__file__).parent / ".env")
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()
