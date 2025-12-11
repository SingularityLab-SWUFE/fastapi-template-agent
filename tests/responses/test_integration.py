"""Integration tests for unified response middleware."""

from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI


async def test_middleware_wraps_success_response():
    """Test middleware wraps successful JSON response."""
    from src.responses import ResponseWrapperMiddleware

    app = FastAPI()
    app.add_middleware(ResponseWrapperMiddleware)

    @app.get("/api/success")
    async def success_endpoint():
        return {"message": "success", "data": {"key": "value"}}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/success")

        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert "msg" in data
        assert "data" in data
        assert data["data"] == {"message": "success", "data": {"key": "value"}}


async def test_middleware_wraps_error_response():
    """Test middleware wraps error JSON response."""
    from src.responses import ResponseWrapperMiddleware
    from fastapi import HTTPException

    app = FastAPI()
    app.add_middleware(ResponseWrapperMiddleware)

    @app.get("/api/error")
    async def error_endpoint():
        raise HTTPException(status_code=400, detail="Bad request")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/error")

        assert response.status_code == 400
        data = response.json()
        assert "code" in data
        assert "msg" in data
        assert "data" in data
        assert "Bad request" in data["msg"]


async def test_middleware_skips_docs_paths():
    """Test middleware skips documentation paths."""
    from src.responses import ResponseWrapperMiddleware

    app = FastAPI()
    app.add_middleware(ResponseWrapperMiddleware)

    @app.get("/api/test")
    async def test_endpoint():
        return {"data": "test"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/docs")
        assert response.status_code == 200

        response = await client.get("/redoc")
        assert response.status_code == 200

        response = await client.get("/openapi.json")
        assert response.status_code == 200


async def test_middleware_leaves_already_wrapped_response():
    """Test middleware doesn't double-wrap already wrapped responses."""
    from src.responses import ResponseWrapperMiddleware
    from src.responses.base import Response

    app = FastAPI()
    app.add_middleware(ResponseWrapperMiddleware)

    @app.get("/api/already-unified")
    async def already_unified_endpoint():
        return Response.success(data={"test": "data"}).model_dump()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/already-unified")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["msg"] == "success"
        assert data["data"] == {"test": "data"}
        assert len(data) == 3
        assert "code" in data and data["code"] == 200
        assert "msg" in data and data["msg"] == "success"
        assert "data" in data and data["data"] == {"test": "data"}


async def test_middleware_with_empty_response():
    """Test middleware handles empty JSON response."""
    from src.responses import ResponseWrapperMiddleware

    app = FastAPI()
    app.add_middleware(ResponseWrapperMiddleware)

    @app.get("/api/empty")
    async def empty_endpoint():
        return {}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/empty")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"] == {}


async def test_middleware_with_list_response():
    """Test middleware wraps list response."""
    from src.responses import ResponseWrapperMiddleware

    app = FastAPI()
    app.add_middleware(ResponseWrapperMiddleware)

    @app.get("/api/list")
    async def list_endpoint():
        return [{"id": 1}, {"id": 2}]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/list")

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == [{"id": 1}, {"id": 2}]


async def test_middleware_with_validation_error():
    """Test middleware wraps validation error."""
    from src.responses import ResponseWrapperMiddleware
    from pydantic import BaseModel

    app = FastAPI()
    app.add_middleware(ResponseWrapperMiddleware)

    class Item(BaseModel):
        name: str
        price: float

    @app.post("/api/item")
    async def create_item(item: Item):
        return item

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/item", json={"name": "test"})

        assert response.status_code == 422
        data = response.json()
        assert "msg" in data
        assert data["code"] == 422


async def test_middleware_preserves_custom_headers():
    """Test middleware preserves custom headers in response."""
    from src.responses import ResponseWrapperMiddleware
    from fastapi.responses import JSONResponse

    app = FastAPI()
    app.add_middleware(ResponseWrapperMiddleware)

    @app.get("/api/with-headers")
    async def with_headers_endpoint():
        return JSONResponse(
            content={"data": "test"},
            headers={"X-Custom-Header": "custom-value"},
        )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/with-headers")

        assert response.status_code == 200
        assert "X-Custom-Header" in response.headers
        assert response.headers["X-Custom-Header"] == "custom-value"


async def test_middleware_handles_business_exception():
    """Test middleware wraps BusinessException responses."""
    from src.handlers import register_exception_handlers
    from src.exceptions import BusinessException, ErrorCode
    from src.responses import ResponseWrapperMiddleware

    app = FastAPI()
    app.add_middleware(ResponseWrapperMiddleware)
    register_exception_handlers(app)

    @app.get("/api/business-error")
    async def business_error():
        raise BusinessException(ErrorCode.BIZ_ORDER_EXPIRED, "Domain failure")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/business-error")

        assert response.status_code == 410
        data = response.json()
        assert data["code"] == ErrorCode.BIZ_ORDER_EXPIRED
        assert data["msg"] == "Domain failure"
