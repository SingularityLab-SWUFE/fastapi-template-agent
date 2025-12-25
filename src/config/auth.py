from pydantic import Field
from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    jwt_secret: str

    jwt_algorithm: str = Field(default="HS256")
    jwt_lifetime_seconds: int = Field(default=1800)
    refresh_token_lifetime_seconds: int = Field(default=2592000)

    oauth_google_client_id: str | None = None
    oauth_google_client_secret: str | None = None
    oauth_github_client_id: str | None = None
    oauth_github_client_secret: str | None = None
