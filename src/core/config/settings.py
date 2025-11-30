from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .app import AppSettings
from .cache import CacheSettings
from .database import DatabaseSettings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="_",
    )

    app: AppSettings = Field(default_factory=AppSettings)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
