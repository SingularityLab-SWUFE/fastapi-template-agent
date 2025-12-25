import pytest
from fastapi import Depends, FastAPI
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import apaginate
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.session import get_session


@pytest.fixture
async def pagination_client(test_db, local_cache, test_user):
    from src.cache import get_cache
    from src.handlers import register_exception_handlers
    from src.responses.middleware import ResponseWrapperMiddleware

    app = FastAPI()
    app.add_middleware(ResponseWrapperMiddleware)
    register_exception_handlers(app)

    async def override_get_session():
        async with test_db() as session:
            yield session

    async def override_get_cache():
        yield local_cache

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_cache] = override_get_cache

    @app.get("/test/users", response_model=Page[User])
    async def list_users(session: AsyncSession = Depends(get_session)):
        return await apaginate(session, select(User))

    add_pagination(app)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_pagination_with_response_middleware(pagination_client):
    response = await pagination_client.get("/test/users?page=1&size=2")
    assert response.status_code == 200

    data = response.json()
    assert data["code"] == 200
    assert data["msg"] == "success"
    assert "data" in data

    page_data = data["data"]
    assert "items" in page_data
    assert "total" in page_data
    assert "page" in page_data
    assert "size" in page_data
    assert len(page_data["items"]) <= 2


@pytest.mark.asyncio
async def test_pagination_default_params(pagination_client):
    response = await pagination_client.get("/test/users")
    assert response.status_code == 200

    data = response.json()
    page_data = data["data"]
    assert page_data["page"] == 1
    assert page_data["size"] == 50


@pytest.mark.asyncio
async def test_pagination_invalid_params(pagination_client):
    response = await pagination_client.get("/test/users?page=0")
    assert response.status_code == 422

    response = await pagination_client.get("/test/users?size=0")
    assert response.status_code == 422
