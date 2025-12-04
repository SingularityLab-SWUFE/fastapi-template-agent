from .settings import Settings


class LazySettings:
    """Lazy-loaded settings instance that respects environment variables."""

    def __init__(self):
        self._settings = None
        self._accessed = False

    @property
    def settings(self):
        if self._settings is None:
            self._settings = Settings()
        return self._settings

    def __getattr__(self, name):
        self._accessed = True
        return getattr(self.settings, name)

    def reset(self):
        """Reset the lazy settings (useful for testing)."""
        self._settings = None
        self._accessed = False


def get_settings():
    """Get settings instance."""
    return Settings()


# For backwards compatibility, expose the lazy settings instance
settings = LazySettings()
"""Overall application settings instance, configured via environment variables."""

__all__ = ["settings", "get_settings"]
