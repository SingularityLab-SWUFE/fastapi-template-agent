from .auth import router as auth_router
from .core import router as core_router
from .oauth import create_oauth_router

__all__ = ["auth_router", "core_router", "create_oauth_router"]
