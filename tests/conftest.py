from pathlib import Path
from typing import AsyncGenerator

import dotenv
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

env_path = Path(__file__).parent.parent / ".env-example"
dotenv.load_dotenv(dotenv_path=env_path)


@pytest.fixture
def base_app() -> FastAPI:
    return FastAPI()


@pytest.fixture
def app_with_middleware(base_app: FastAPI) -> FastAPI:
    from src.responses import ResponseWrapperMiddleware

    base_app.add_middleware(ResponseWrapperMiddleware)
    return base_app


@pytest.fixture
def app_with_handlers(base_app: FastAPI) -> FastAPI:
    from src.handlers import register_exception_handlers

    register_exception_handlers(base_app)
    return base_app


@pytest.fixture
def full_app(base_app: FastAPI) -> FastAPI:
    from src.responses import ResponseWrapperMiddleware
    from src.handlers import register_exception_handlers

    base_app.add_middleware(ResponseWrapperMiddleware)
    register_exception_handlers(base_app)
    return base_app


@pytest.fixture
async def async_client(full_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=full_app), base_url="http://test"
    ) as client:
        yield client
