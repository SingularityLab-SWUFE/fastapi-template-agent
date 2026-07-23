import os
from pathlib import Path
import re
from typing import Any

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from .app import AppSettings
from .auth import AuthSettings
from .cache import CacheSettings
from .database import DatabaseSettings
from .log import LogSettings


_PLACEHOLDER_RE: re.Pattern[str] = re.compile(r"^\$([A-Za-z_][A-Za-z0-9_]*)$")


class AppYamlConfigSettingsSource(YamlConfigSettingsSource):
    """YAML config source that strips unresolved $ENV placeholders.

    For secret configuration,
    this project suggests using explicit $ENV placeholders in yaml config file,
    making the yaml config self-documented and safe to VCS,
    but will NOT attempt to inject env to the yaml file at runtime.

    Placeholder values (e.g. ``$DB_HOST``) are removed structurally from the env,
    allowing lower-priority sources (env vars, dotenv)
    to fill in the values via pydantic-settings fallthrough.
    """

    _REMOVE = object()

    def __call__(self) -> dict[str, Any]:
        data = self._prune_env_node(super().__call__())
        return data if data is not self._REMOVE else {}

    @classmethod
    def _prune_env_node(cls, value: Any) -> Any:
        match value:
            case str() if _PLACEHOLDER_RE.match(value):
                return cls._REMOVE
            case list():
                items = [cls._prune_env_node(item) for item in value]
                return cls._REMOVE if cls._REMOVE in items else items
            case dict():
                stripped = {
                    k: v
                    for k, val in value.items()
                    if (v := cls._prune_env_node(val)) is not cls._REMOVE
                }
                return stripped if stripped else cls._REMOVE
            case _:
                return value

    @classmethod
    def resolve(
        cls,
        settings_cls: type[BaseSettings],
        dotenv_settings: DotEnvSettingsSource,
    ) -> "AppYamlConfigSettingsSource | None":
        """Bootstrap yaml config source for the app, if APP_CONFIG_FILE set."""
        config_file = os.environ.get("APP_CONFIG_FILE")
        if config_file is None:
            config_file = dotenv_settings.env_vars.get("app_config_file")
        if not config_file:
            return None
        yaml_file = Path(config_file)
        if not yaml_file.is_file():
            raise FileNotFoundError(f"APP_CONFIG_FILE does not exist: {yaml_file}")
        return cls(settings_cls, yaml_file=yaml_file)


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

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: DotEnvSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        sources: list[PydanticBaseSettingsSource] = [
            init_settings,
            env_settings,
            dotenv_settings,
        ]
        yaml_source = AppYamlConfigSettingsSource.resolve(settings_cls, dotenv_settings)
        if yaml_source:
            sources.append(yaml_source)
        sources.append(file_secret_settings)
        return tuple(sources)
