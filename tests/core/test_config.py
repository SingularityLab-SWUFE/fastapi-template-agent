from pathlib import Path

import pytest


@pytest.fixture
def env_example_path():
    return Path(__file__).parent.parent.parent / ".env-example"


@pytest.fixture(autouse=True)
def load_env_var(env_example_path, monkeypatch):
    """
    Load environment variables from the .env-example file before each test.
    This mocks external environment variables injection such as:

    - 1. kubernetes config map/secret `envFrom`
    - 2. docker-compose `environment` or `env_file`
    - 3. CI/CD pipeline env variables (`export`)

    Environment variables take precedence over .env file values,
    guranteed by pydantic settings.
    """
    import dotenv

    dotenv.load_dotenv(dotenv_path=env_example_path)
    monkeypatch.setenv("APP__NAME", "Test App Loading env var")


def test_settings_created_by_env_file(env_example_path):
    """
    Use specified env file to create a custom Settings instance.
    """
    from src.config.settings import Settings

    custom_settings = Settings(_env_file=env_example_path)

    assert (
        custom_settings.app.name == "Test App Loading env var"
    )  # overwrite by env var
    assert custom_settings.db.host == "db"


def test_settings_loading_env_variables():
    """
    Use env variables to create the Settings instance.
    """
    from src.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    assert settings.app.name == "Test App Loading env var"
    assert settings.db.host == "db"
