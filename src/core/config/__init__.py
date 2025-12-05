from functools import lru_cache

from .settings import Settings


@lru_cache()
def get_settings() -> Settings:
    """Get settings instance via dependency injection."""
    return Settings()


__all__ = ["get_settings"]
