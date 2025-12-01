import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.core.middleware.exception_middleware import ExceptionMiddleware
from src.core.handlers.exceptions import BusinessException

@pytest.mark.asyncio
async def test_exception_middleware_registered():
    from src.main import app

    middleware_found = False
    for middleware_cls in app.user_middleware:
        if middleware_cls.cls == ExceptionMiddleware:
            middleware_found = True
            break

    assert middleware_found, "ExceptionMiddleware should be registered in the app"

@pytest.mark.asyncio
async def test_exception_middleware_with_business_exception():
    app = FastAPI()

    @app.exception_handler(BusinessException)
    async def business_exception_handler(request, exc):
        from src.core.responses.schemas import ErrorResponse
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=200,
            content=ErrorResponse.error(exc.code, exc.message).model_dump()
        )

    app.add_middleware(ExceptionMiddleware)

    @app.get("/business-error")
    async def business_error():
        raise BusinessException(code=1001, message="Custom business error")

    client = TestClient(app)
    response = client.get("/business-error")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 1001
    assert data["msg"] == "Custom business error"

@pytest.mark.asyncio
async def test_middleware_does_not_interfere_normal_responses():
    app = FastAPI()

    app.add_middleware(ExceptionMiddleware)

    @app.get("/normal")
    async def normal_response():
        return {"status": "ok"}

    client = TestClient(app)
    response = client.get("/normal")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_middleware_handles_http_exceptions():
    from fastapi import HTTPException
    from src.core.responses.schemas import ErrorResponse
    from fastapi.responses import JSONResponse

    app = FastAPI()

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse.error(exc.status_code, exc.detail).model_dump()
        )

    app.add_middleware(ExceptionMiddleware)

    @app.get("/http-error")
    async def http_error():
        raise HTTPException(status_code=404, detail="Resource not found")

    client = TestClient(app)
    response = client.get("/http-error")

    assert response.status_code == 404
    data = response.json()
    assert data["code"] == 404
    assert "Resource not found" in data["msg"]

@pytest.mark.asyncio
async def test_middleware_handles_value_errors():
    app = FastAPI()
    app.add_middleware(ExceptionMiddleware)

    @app.get("/value-error")
    async def value_error():
        raise ValueError("Invalid value provided")

    client = TestClient(app)
    response = client.get("/value-error")

    assert response.status_code == 400
    data = response.json()
    assert data["code"] == 400
    assert "Invalid value provided" in data["msg"]
