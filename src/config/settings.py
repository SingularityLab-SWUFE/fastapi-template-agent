from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .app import AppSettings
from .auth import AuthSettings
from .cache import CacheSettings
from .database import DatabaseSettings
from .log import LogSettings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        # avoid snake_case conflict
        env_nested_delimiter="__",
    )

    app: AppSettings = Field(default_factory=AppSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    log: LogSettings = Field(default_factory=LogSettings)
