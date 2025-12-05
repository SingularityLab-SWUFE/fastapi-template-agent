from .settings import Settings


def get_settings() -> Settings:
    """Get settings instance via dependency injection."""
    return Settings()


__all__ = ["get_settings"]
