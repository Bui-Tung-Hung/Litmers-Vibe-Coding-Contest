from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import get_settings
from backend.database import init_db

settings = get_settings()

app = FastAPI(title="Litmer API", version="1.0.0")

# CORS - Allow Vercel and localhost
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allow all Vercel deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """Initialize database on startup"""
    init_db()


@app.get("/")
def read_root():
    return {"message": "Litmer API is running", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Import routers after app initialization to avoid circular imports
try:
    from backend.api import (
        auth,
        users,
        teams,
        projects,
        issues,
        comments,
        ai,
        notifications,
        dashboard
    )
    
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(users.router, prefix="/api/users", tags=["users"])
    app.include_router(teams.router, prefix="/api/teams", tags=["teams"])
    app.include_router(projects.router, prefix="/api", tags=["projects"])
    app.include_router(issues.router, prefix="/api", tags=["issues"])
    app.include_router(comments.router, prefix="/api", tags=["comments"])
    app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
    app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
    app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
except ImportError as e:
    print(f"Warning: Failed to import routers: {e}")
    print("Application will run with basic endpoints only")
