from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    jwt_secret_key: str
    jwt_algorithm: str = Field(default="HS256")

    # Fields for environment variables (minutes and days)
    jwt_access_token_expire_minutes: int = Field(default=30)
    jwt_refresh_token_expire_days: int = Field(default=7)

    # Computed fields (seconds)
    jwt_lifetime_seconds: int = Field(default=1800)
    refresh_token_lifetime_seconds: int = Field(default=2592000)

    oauth_google_client_id: str | None = None
    oauth_google_client_secret: str | None = None
    oauth_github_client_id: str | None = None
    oauth_github_client_secret: str | None = None

    @model_validator(mode="after")
    def compute_lifetime_seconds(self) -> "AuthSettings":
        """Compute seconds from minutes/days."""
        if self.jwt_lifetime_seconds == 1800:  # default value
            self.jwt_lifetime_seconds = self.jwt_access_token_expire_minutes * 60
        if self.refresh_token_lifetime_seconds == 2592000:  # default value
            self.refresh_token_lifetime_seconds = self.jwt_refresh_token_expire_days * 24 * 60 * 60
        return self
