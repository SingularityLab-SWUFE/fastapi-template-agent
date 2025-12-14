import pytest
from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from httpx import AsyncClient, ASGITransport

from src.exceptions import BusinessException, ErrorCode
from src.handlers import register_exception_handlers


def test_register_all_handlers(base_app: FastAPI):
    register_exception_handlers(base_app)

    assert Exception in base_app.exception_handlers

    handler = base_app.exception_handlers[Exception]
    assert callable(handler)


class TestBusinessExceptionHandler:
    @pytest.mark.asyncio
    async def test_business_exception_integration(self, full_app: FastAPI):
        @full_app.get("/test")
        async def test_endpoint():
            raise BusinessException(ErrorCode.AUTH_ACCOUNT_LOCKED, "I'm a teapot")

        async with AsyncClient(
            transport=ASGITransport(app=full_app), base_url="http://test"
        ) as client:
            response = await client.get("/test")

            assert response.status_code == 403
            data = response.json()
            assert data["code"] == ErrorCode.AUTH_ACCOUNT_LOCKED
            assert data["msg"] == "I'm a teapot"

    @pytest.mark.asyncio
    async def test_business_exception_with_data(self, full_app: FastAPI):
        @full_app.get("/test")
        async def test_endpoint():
            raise BusinessException(
                ErrorCode.DATA_VALIDATION_FAILED,
                "Validation failed",
                data={"field": "email"},
            )

        async with AsyncClient(
            transport=ASGITransport(app=full_app), base_url="http://test"
        ) as client:
            response = await client.get("/test")

            assert response.status_code == 422
            data = response.json()
            assert data["code"] == ErrorCode.DATA_VALIDATION_FAILED
            assert data["data"] == {"field": "email"}

    @pytest.mark.asyncio
    async def test_business_exception_unmapped_code(self, full_app: FastAPI):
        @full_app.get("/test")
        async def test_endpoint():
            raise BusinessException(ErrorCode.SYS_INTERNAL_ERROR, "Internal error")

        transport = ASGITransport(app=full_app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

            assert response.status_code == 500
            data = response.json()
            assert data["code"] == ErrorCode.SYS_INTERNAL_ERROR
            assert data["msg"] == "Internal error"


class TestHTTPExceptionHandler:
    @pytest.mark.asyncio
    async def test_http_exception_integration(self, full_app: FastAPI):
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
    async def test_http_exception_with_dict_detail(self, full_app: FastAPI):
        @full_app.get("/test")
        async def test_endpoint():
            raise HTTPException(
                status_code=400, detail={"msg": "Bad request", "field": "email"}
            )

        async with AsyncClient(
            transport=ASGITransport(app=full_app), base_url="http://test"
        ) as client:
            response = await client.get("/test")

            data = response.json()
            assert data["msg"] == "Bad request"

    @pytest.mark.asyncio
    async def test_http_exception_with_list_detail(self, full_app: FastAPI):
        @full_app.get("/test")
        async def test_endpoint():
            raise HTTPException(
                status_code=422, detail=["Email is required", "Password is required"]
            )

        async with AsyncClient(
            transport=ASGITransport(app=full_app), base_url="http://test"
        ) as client:
            response = await client.get("/test")

            data = response.json()
            assert data["msg"] == "Email is required"

    @pytest.mark.asyncio
    async def test_http_exception_with_none_detail(self, full_app: FastAPI):
        @full_app.get("/test")
        async def test_endpoint():
            raise HTTPException(status_code=500, detail=None)

        transport = ASGITransport(app=full_app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

            data = response.json()
            assert data["msg"] == "Internal Server Error"


class TestValidationExceptionHandler:
    @pytest.mark.asyncio
    async def test_validation_exception_integration(self, full_app: FastAPI):
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

    @pytest.mark.asyncio
    async def test_validation_multiple_errors(self, full_app: FastAPI):
        @full_app.get("/test")
        async def test_endpoint():
            raise RequestValidationError(
                errors=[
                    {
                        "loc": ["body", "email"],
                        "msg": "Invalid email",
                        "type": "value_error",
                    },
                    {
                        "loc": ["body", "password"],
                        "msg": "Password too short",
                        "type": "value_error",
                    },
                ]
            )

        async with AsyncClient(
            transport=ASGITransport(app=full_app), base_url="http://test"
        ) as client:
            response = await client.get("/test")

            data = response.json()
            assert len(data["data"]["validation_errors"]) == 2

    @pytest.mark.asyncio
    async def test_validation_nested_field(self, full_app: FastAPI):
        @full_app.get("/test")
        async def test_endpoint():
            raise RequestValidationError(
                errors=[
                    {
                        "loc": ["body", "user", "email"],
                        "msg": "Invalid email",
                        "type": "value_error",
                    }
                ]
            )

        async with AsyncClient(
            transport=ASGITransport(app=full_app), base_url="http://test"
        ) as client:
            response = await client.get("/test")

            data = response.json()
            assert data["data"]["validation_errors"][0]["field"] == "user.email"


class TestUnknownExceptionHandler:
    @pytest.mark.asyncio
    async def test_unknown_exception_integration(self, full_app: FastAPI):
        @full_app.get("/test")
        async def test_endpoint():
            raise RuntimeError("Unexpected error")

        transport = ASGITransport(app=full_app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

        assert response.status_code == 500
        data = response.json()
        assert data["code"] == 500
        assert data["msg"] == "Internal server error"
        assert data["data"]["error_type"] == "RuntimeError"
