from fastapi import APIRouter
from httpx_oauth.clients.github import GitHubOAuth2
from httpx_oauth.clients.google import GoogleOAuth2

from src.config import Settings

from src.auth import fastapi_users
from src.auth.backend import auth_backend


def create_oauth_router(settings: Settings) -> APIRouter:
    """Create OAuth router with settings."""
    oauth_router = APIRouter()

    if (
        settings.auth.oauth_google_client_id
        and settings.auth.oauth_google_client_secret
    ):
        google_oauth_client = GoogleOAuth2(
            settings.auth.oauth_google_client_id,
            settings.auth.oauth_google_client_secret,
        )

        oauth_router.include_router(
            fastapi_users.get_oauth_router(
                google_oauth_client,
                auth_backend,
                settings.auth.jwt_secret,
                associate_by_email=True,
            ),
            prefix="/google",
            tags=["auth"],
        )

    if (
        settings.auth.oauth_github_client_id
        and settings.auth.oauth_github_client_secret
    ):
        github_oauth_client = GitHubOAuth2(
            settings.auth.oauth_github_client_id,
            settings.auth.oauth_github_client_secret,
        )

        oauth_router.include_router(
            fastapi_users.get_oauth_router(
                github_oauth_client,
                auth_backend,
                settings.auth.jwt_secret,
                associate_by_email=True,
            ),
            prefix="/github",
            tags=["auth"],
        )

    return oauth_router
