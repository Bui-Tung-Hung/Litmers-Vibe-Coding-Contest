from .auth import router as auth_router
from .users import router as users_router
from .teams import router as teams_router
from .projects import router as projects_router
from .issues import router as issues_router
from .comments import router as comments_router
from .ai import router as ai_router
from .notifications import router as notifications_router
from .dashboard import router as dashboard_router

__all__ = [
    "auth_router",
    "users_router",
    "teams_router",
    "projects_router",
    "issues_router",
    "comments_router",
    "ai_router",
    "notifications_router",
    "dashboard_router",
]
