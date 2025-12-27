import pytest
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from httpx import AsyncClient, ASGITransport
from src.shared.errors import ErrorCode
from src.exceptions import BusinessException


@pytest.mark.parametrize(
    "endpoint,expected_status,expected_data",
    [
        ("/api/success", 200, {"message": "success", "data": {"key": "value"}}),
        ("/api/list", 200, [{"id": 1}, {"id": 2}]),
    ],
)
@pytest.mark.asyncio
async def test_middleware_wraps_success_responses(
    app_with_middleware: FastAPI, endpoint, expected_status, expected_data
):
    @app_with_middleware.get("/api/success")
    async def success_endpoint():
        return {"message": "success", "data": {"key": "value"}}

    @app_with_middleware.get("/api/list")
    async def list_endpoint():
        return [{"id": 1}, {"id": 2}]

    async with AsyncClient(
        transport=ASGITransport(app=app_with_middleware), base_url="http://test"
    ) as client:
        response = await client.get(endpoint)

        assert response.status_code == expected_status
        data = response.json()
        assert data["data"] == expected_data


@pytest.mark.asyncio
async def test_middleware_wraps_error_response(app_with_middleware: FastAPI):
    @app_with_middleware.get("/api/error")
    async def error_endpoint():
        raise HTTPException(status_code=400, detail="Bad request")

    async with AsyncClient(
        transport=ASGITransport(app=app_with_middleware), base_url="http://test"
    ) as client:
        response = await client.get("/api/error")

        assert response.status_code == 400
        data = response.json()
        assert data == {"detail": "Bad request"}


@pytest.mark.asyncio
async def test_middleware_skips_docs_paths(app_with_middleware: FastAPI):
    @app_with_middleware.get("/api/test")
    async def test_endpoint():
        return {"data": "test"}

    async with AsyncClient(
        transport=ASGITransport(app=app_with_middleware), base_url="http://test"
    ) as client:
        response = await client.get("/docs")
        assert response.status_code == 200

        response = await client.get("/redoc")
        assert response.status_code == 200

        response = await client.get("/openapi.json")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_middleware_leaves_already_wrapped_response(
    app_with_middleware: FastAPI,
):
    from src.responses.base import Response

    @app_with_middleware.get("/api/already-unified")
    async def already_unified_endpoint():
        return Response.success(data={"test": "data"}).model_dump()

    async with AsyncClient(
        transport=ASGITransport(app=app_with_middleware), base_url="http://test"
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


@pytest.mark.asyncio
async def test_middleware_with_empty_response(app_with_middleware: FastAPI):
    @app_with_middleware.get("/api/empty")
    async def empty_endpoint():
        return {}

    async with AsyncClient(
        transport=ASGITransport(app=app_with_middleware), base_url="http://test"
    ) as client:
        response = await client.get("/api/empty")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"] == {}


@pytest.mark.parametrize(
    "endpoint,exception,status_code",
    [
        (
            "/test",
            BusinessException(ErrorCode.AUTH_ACCOUNT_LOCKED, "I'm a teapot"),
            403,
        ),
        (
            "/test",
            BusinessException(
                ErrorCode.DATA_VALIDATION_FAILED,
                "Validation failed",
                data={"field": "email"},
            ),
            422,
        ),
    ],
)
@pytest.mark.asyncio
async def test_business_exceptions(full_app: FastAPI, endpoint, exception, status_code):
    @full_app.get(endpoint)
    async def test_endpoint():
        raise exception

    async with AsyncClient(
        transport=ASGITransport(app=full_app), base_url="http://test"
    ) as client:
        response = await client.get(endpoint)

        assert response.status_code == status_code


@pytest.mark.asyncio
async def test_http_exception_integration(full_app: FastAPI):
    @full_app.get("/test")
    async def test_endpoint():
        raise HTTPException(status_code=404, detail="Resource not found")

    async with AsyncClient(
        transport=ASGITransport(app=full_app), base_url="http://test"
    ) as client:
        response = await client.get("/test")

        assert response.status_code == 404
        data = response.json()
        assert data["code"] == 404
        assert data["msg"] == "Resource not found"


@pytest.mark.asyncio
async def test_validation_exception_integration(full_app: FastAPI):
    @full_app.get("/test")
    async def test_endpoint():
        raise RequestValidationError(
            errors=[
                {
                    "loc": ["body", "email"],
                    "msg": "Invalid email",
                    "type": "value_error",
                }
            ]
        )

    async with AsyncClient(
        transport=ASGITransport(app=full_app), base_url="http://test"
    ) as client:
        response = await client.get("/test")

        assert response.status_code == 422
        data = response.json()
        assert data["code"] == 422
        assert data["msg"] == "Validation failed"
        assert "validation_errors" in data["data"]
