import pytest
from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from httpx import AsyncClient, ASGITransport

from src.exceptions import BusinessException, ErrorCode
from src.handlers import register_exception_handlers


class TestIntegration:
    @pytest.mark.asyncio
    async def test_register_all_handlers(self):
        app = FastAPI()
        register_exception_handlers(app)

        assert Exception in app.exception_handlers

        handler = app.exception_handlers[Exception]
        assert callable(handler)

    @pytest.mark.asyncio
    async def test_business_exception_integration(self):
        from src.responses import ResponseWrapperMiddleware

        app = FastAPI()
        app.add_middleware(ResponseWrapperMiddleware)
        register_exception_handlers(app)

        @app.get("/test")
        async def test_endpoint():
            raise BusinessException(ErrorCode.AUTH_ACCOUNT_LOCKED, "I'm a teapot")

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/test")

            assert response.status_code == 403
            data = response.json()
            assert data["code"] == ErrorCode.AUTH_ACCOUNT_LOCKED
            assert data["msg"] == "I'm a teapot"

    @pytest.mark.asyncio
    async def test_http_exception_integration(self):
        from src.responses import ResponseWrapperMiddleware

        app = FastAPI()
        app.add_middleware(ResponseWrapperMiddleware)
        register_exception_handlers(app)

        @app.get("/test")
        async def test_endpoint():
            raise HTTPException(status_code=404, detail="Resource not found")

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/test")

            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 404
            assert data["msg"] == "Resource not found"

    @pytest.mark.asyncio
    async def test_validation_exception_integration(self):
        from src.responses import ResponseWrapperMiddleware

        app = FastAPI()
        app.add_middleware(ResponseWrapperMiddleware)
        register_exception_handlers(app)

        @app.get("/test")
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
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/test")

            assert response.status_code == 422
            data = response.json()
            assert data["code"] == 422
            assert data["msg"] == "Validation failed"
            assert "validation_errors" in data["data"]

    @pytest.mark.asyncio
    async def test_unknown_exception_integration(self):
        from src.responses import ResponseWrapperMiddleware

        app = FastAPI()
        app.add_middleware(ResponseWrapperMiddleware)
        register_exception_handlers(app)

        @app.get("/test")
        async def test_endpoint():
            raise RuntimeError("Unexpected error")

        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

        assert response.status_code == 500
        data = response.json()
        assert data["code"] == 500
        assert data["msg"] == "Internal server error"
        assert data["data"]["error_type"] == "RuntimeError"

    @pytest.mark.asyncio
    async def test_successful_response_not_wrapped_as_error(self):
        from src.responses import ResponseWrapperMiddleware

        app = FastAPI()
        app.add_middleware(ResponseWrapperMiddleware)
        register_exception_handlers(app)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/test")

            assert response.status_code == 200
            data = response.json()
            assert data["msg"] == "success"
            assert data["data"]["message"] == "success"

    @pytest.mark.asyncio
    async def test_business_exception_with_data(self):
        from src.responses import ResponseWrapperMiddleware

        app = FastAPI()
        app.add_middleware(ResponseWrapperMiddleware)
        register_exception_handlers(app)

        @app.get("/test")
        async def test_endpoint():
            raise BusinessException(
                ErrorCode.DATA_VALIDATION_FAILED,
                "Validation failed",
                data={"field": "email"},
            )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/test")

            assert response.status_code == 422
            data = response.json()
            assert data["code"] == ErrorCode.DATA_VALIDATION_FAILED
            assert data["data"] == {"field": "email"}

    @pytest.mark.asyncio
    async def test_http_exception_with_dict_detail(self):
        from src.responses import ResponseWrapperMiddleware

        app = FastAPI()
        app.add_middleware(ResponseWrapperMiddleware)
        register_exception_handlers(app)

        @app.get("/test")
        async def test_endpoint():
            raise HTTPException(
                status_code=400, detail={"msg": "Bad request", "field": "email"}
            )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/test")

            data = response.json()
            assert data["msg"] == "Bad request"

    @pytest.mark.asyncio
    async def test_http_exception_with_list_detail(self):
        from src.responses import ResponseWrapperMiddleware

        app = FastAPI()
        app.add_middleware(ResponseWrapperMiddleware)
        register_exception_handlers(app)

        @app.get("/test")
        async def test_endpoint():
            raise HTTPException(
                status_code=422, detail=["Email is required", "Password is required"]
            )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/test")

            data = response.json()
            assert data["msg"] == "Email is required"

    @pytest.mark.asyncio
    async def test_http_exception_with_none_detail(self):
        from src.responses import ResponseWrapperMiddleware

        app = FastAPI()
        app.add_middleware(ResponseWrapperMiddleware)
        register_exception_handlers(app)

        @app.get("/test")
        async def test_endpoint():
            raise HTTPException(status_code=500, detail=None)

        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

            data = response.json()
            assert data["msg"] == "Internal Server Error"

    @pytest.mark.asyncio
    async def test_validation_multiple_errors(self):
        from src.responses import ResponseWrapperMiddleware

        app = FastAPI()
        app.add_middleware(ResponseWrapperMiddleware)
        register_exception_handlers(app)

        @app.get("/test")
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
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/test")

            data = response.json()
            assert len(data["data"]["validation_errors"]) == 2

    @pytest.mark.asyncio
    async def test_validation_nested_field(self):
        from src.responses import ResponseWrapperMiddleware

        app = FastAPI()
        app.add_middleware(ResponseWrapperMiddleware)
        register_exception_handlers(app)

        @app.get("/test")
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
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/test")

            data = response.json()
            assert data["data"]["validation_errors"][0]["field"] == "user.email"

    @pytest.mark.asyncio
    async def test_business_exception_unmapped_code(self):
        from src.responses import ResponseWrapperMiddleware

        app = FastAPI()
        app.add_middleware(ResponseWrapperMiddleware)
        register_exception_handlers(app)

        @app.get("/test")
        async def test_endpoint():
            raise BusinessException(ErrorCode.SYS_INTERNAL_ERROR, "Internal error")

        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

            assert response.status_code == 500
            data = response.json()
            assert data["code"] == ErrorCode.SYS_INTERNAL_ERROR
            assert data["msg"] == "Internal error"
