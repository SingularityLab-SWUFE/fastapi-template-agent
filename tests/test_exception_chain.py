import json
import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from httpx import AsyncClient, ASGITransport

from src.exceptions import BusinessException
from src.handlers import (
    BusinessExceptionHandler,
    FallbackExceptionHandler,
    HTTPExceptionHandler,
    ValidationExceptionHandler,
    build_exception_chain,
    register_exception_handlers,
)
from src.responses.base import Response


class TestBusinessExceptionHandler:
    @pytest.mark.asyncio
    async def test_handles_business_exception(self):
        handler = BusinessExceptionHandler()
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

        exc = BusinessException(business_code=422, msg="Invalid input")
        assert handler.can_handle(exc)

        response = await handler.handle(request, exc)
        assert response.status_code == 422

        body = json.loads(response.body)
        assert body["code"] == 422
        assert body["msg"] == "Invalid input"
        assert body["data"] is None

    @pytest.mark.asyncio
    async def test_handles_invalid_code(self):
        handler = BusinessExceptionHandler()
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

        exc = BusinessException(business_code=9999, msg="Invalid code")
        response = await handler.handle(request, exc)

        assert response.status_code == 400

        body = json.loads(response.body)
        assert body["code"] == 9999
        assert body["msg"] == "Invalid code"

    @pytest.mark.asyncio
    async def test_handles_mapped_code(self):
        handler = BusinessExceptionHandler()
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

        exc = BusinessException(business_code=401, msg="Unauthorized")
        response = await handler.handle(request, exc)

        assert response.status_code == 401
        body = json.loads(response.body)
        assert body["code"] == 401
        assert body["msg"] == "Unauthorized"

    @pytest.mark.asyncio
    async def test_handles_exception_with_data(self):
        handler = BusinessExceptionHandler()
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

        exc = BusinessException(business_code=422, msg="Validation failed", data={"field": "email"})
        response = await handler.handle(request, exc)

        body = json.loads(response.body)
        assert body["data"] == {"field": "email"}

    @pytest.mark.asyncio
    async def test_cannot_handle_other_exceptions(self):
        handler = BusinessExceptionHandler()

        assert not handler.can_handle(ValueError("test"))
        assert not handler.can_handle(HTTPException(status_code=404, detail="Not found"))


class TestHTTPExceptionHandler:
    @pytest.mark.asyncio
    async def test_handles_http_exception(self):
        handler = HTTPExceptionHandler()
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

        exc = HTTPException(status_code=404, detail="Not found")
        assert handler.can_handle(exc)

        response = await handler.handle(request, exc)
        assert response.status_code == 404

        body = json.loads(response.body)
        assert body["code"] == 404
        assert body["msg"] == "Not found"
        assert body["data"] is None

    @pytest.mark.asyncio
    async def test_handles_http_exception_with_dict_detail(self):
        handler = HTTPExceptionHandler()
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

        exc = HTTPException(status_code=400, detail={"msg": "Bad request", "field": "email"})
        response = await handler.handle(request, exc)

        body = json.loads(response.body)
        assert body["msg"] == "Bad request"

    @pytest.mark.asyncio
    async def test_handles_http_exception_with_list_detail(self):
        handler = HTTPExceptionHandler()
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

        exc = HTTPException(status_code=422, detail=["Email is required", "Password is required"])
        response = await handler.handle(request, exc)

        body = json.loads(response.body)
        assert body["msg"] == "Email is required"

    @pytest.mark.asyncio
    async def test_handles_http_exception_with_complex_detail(self):
        handler = HTTPExceptionHandler()
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

        exc = HTTPException(status_code=500, detail=None)
        response = await handler.handle(request, exc)

        body = json.loads(response.body)
        assert body["msg"] == "Internal Server Error"

    @pytest.mark.asyncio
    async def test_cannot_handle_other_exceptions(self):
        handler = HTTPExceptionHandler()

        assert not handler.can_handle(BusinessException(business_code=400, msg="test"))
        assert not handler.can_handle(ValueError("test"))


class TestValidationExceptionHandler:
    @pytest.mark.asyncio
    async def test_handles_validation_error(self):
        handler = ValidationExceptionHandler()
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

        exc = RequestValidationError(errors=[
            {"loc": ["body", "email"], "msg": "Invalid email", "type": "value_error"}
        ])
        assert handler.can_handle(exc)

        response = await handler.handle(request, exc)
        assert response.status_code == 422

        body = json.loads(response.body)
        assert body["code"] == 422
        assert body["msg"] == "Validation failed"
        assert "validation_errors" in body["data"]
        assert body["data"]["validation_errors"][0]["field"] == "email"
        assert body["data"]["validation_errors"][0]["message"] == "Invalid email"
        assert body["data"]["validation_errors"][0]["type"] == "value_error"

    @pytest.mark.asyncio
    async def test_handles_multiple_validation_errors(self):
        handler = ValidationExceptionHandler()
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

        exc = RequestValidationError(errors=[
            {"loc": ["body", "email"], "msg": "Invalid email", "type": "value_error"},
            {"loc": ["body", "password"], "msg": "Password too short", "type": "value_error"},
        ])
        response = await handler.handle(request, exc)

        body = json.loads(response.body)
        assert len(body["data"]["validation_errors"]) == 2

    @pytest.mark.asyncio
    async def test_handles_nested_field_validation_errors(self):
        handler = ValidationExceptionHandler()
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

        exc = RequestValidationError(errors=[
            {"loc": ["body", "user", "email"], "msg": "Invalid email", "type": "value_error"}
        ])
        response = await handler.handle(request, exc)

        body = json.loads(response.body)
        assert body["data"]["validation_errors"][0]["field"] == "user.email"

    @pytest.mark.asyncio
    async def test_cannot_handle_other_exceptions(self):
        handler = ValidationExceptionHandler()

        assert not handler.can_handle(BusinessException(business_code=400, msg="test"))
        assert not handler.can_handle(HTTPException(status_code=422, detail="Bad"))


class TestFallbackExceptionHandler:
    @pytest.mark.asyncio
    async def test_handles_any_exception(self):
        handler = FallbackExceptionHandler()
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

        exc = ValueError("Unexpected error")
        assert handler.can_handle(exc)

        response = await handler.handle(request, exc)
        assert response.status_code == 500

        body = json.loads(response.body)
        assert body["code"] == 500
        assert body["msg"] == "Internal server error"
        assert body["data"]["error_type"] == "ValueError"
        assert "error_id" in body["data"]

    @pytest.mark.asyncio
    async def test_handles_exception_without_message(self):
        handler = FallbackExceptionHandler()
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

        exc = Exception()
        response = await handler.handle(request, exc)

        body = json.loads(response.body)
        assert body["code"] == 500
        assert body["msg"] == "Internal server error"

    @pytest.mark.asyncio
    async def test_can_handle_always_true(self):
        handler = FallbackExceptionHandler()

        assert handler.can_handle(ValueError("test"))
        assert handler.can_handle(BusinessException(business_code=400, msg="test"))
        assert handler.can_handle(HTTPException(status_code=404, detail="Not found"))
        assert handler.can_handle(RequestValidationError(errors=[]))


class TestHandlerChain:
    @pytest.mark.asyncio
    async def test_first_matching_handler_wins(self):
        handlers = [
            BusinessExceptionHandler(),
            HTTPExceptionHandler(),
            ValidationExceptionHandler(),
            FallbackExceptionHandler(),
        ]

        chain = build_exception_chain(handlers)
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

        exc = BusinessException(business_code=400, msg="Business error")
        response = await chain(request, exc)

        assert response.status_code == 400
        body = json.loads(response.body)
        assert body["code"] == 400
        assert body["msg"] == "Business error"

    @pytest.mark.asyncio
    async def test_http_exception_handler_wins(self):
        handlers = [
            BusinessExceptionHandler(),
            HTTPExceptionHandler(),
            ValidationExceptionHandler(),
            FallbackExceptionHandler(),
        ]

        chain = build_exception_chain(handlers)
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

        exc = HTTPException(status_code=404, detail="Not found")
        response = await chain(request, exc)

        assert response.status_code == 404
        body = json.loads(response.body)
        assert body["code"] == 404
        assert body["msg"] == "Not found"

    @pytest.mark.asyncio
    async def test_validation_exception_handler_wins(self):
        handlers = [
            BusinessExceptionHandler(),
            HTTPExceptionHandler(),
            ValidationExceptionHandler(),
            FallbackExceptionHandler(),
        ]

        chain = build_exception_chain(handlers)
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

        exc = RequestValidationError(errors=[
            {"loc": ["body", "email"], "msg": "Invalid", "type": "value_error"}
        ])
        response = await chain(request, exc)

        assert response.status_code == 422
        body = json.loads(response.body)
        assert body["code"] == 422
        assert body["msg"] == "Validation failed"

    @pytest.mark.asyncio
    async def test_fallback_for_unknown_exception(self):
        handlers = [
            BusinessExceptionHandler(),
            HTTPExceptionHandler(),
            ValidationExceptionHandler(),
            FallbackExceptionHandler(),
        ]

        chain = build_exception_chain(handlers)
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

        exc = RuntimeError("Unknown error")
        response = await chain(request, exc)

        assert response.status_code == 500
        body = json.loads(response.body)
        assert body["code"] == 500
        assert body["msg"] == "Internal server error"
        assert body["data"]["error_type"] == "RuntimeError"

    @pytest.mark.asyncio
    async def test_fallback_for_empty_chain(self):
        chain = build_exception_chain([])
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})

        exc = ValueError("test")
        response = await chain(request, exc)

        assert response.status_code == 500
        body = json.loads(response.body)
        assert body["code"] == 500


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
            raise BusinessException(business_code=418, msg="I'm a teapot")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/test")

            assert response.status_code == 418
            data = response.json()
            assert data["code"] == 418
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

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
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
            raise RequestValidationError(errors=[
                {"loc": ["body", "email"], "msg": "Invalid email", "type": "value_error"}
            ])

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
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

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/test")

            assert response.status_code == 200
            data = response.json()
            assert data["msg"] == "success"
            assert data["data"]["message"] == "success"
