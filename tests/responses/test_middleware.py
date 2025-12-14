"""Test unified response middleware."""

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from httpx import ASGITransport, AsyncClient

from src.responses.middleware import ResponseWrapperMiddleware


@pytest.mark.asyncio
async def test_middleware_preserves_custom_headers(app_with_middleware: FastAPI):
    @app_with_middleware.get("/api/with-headers")
    async def with_headers_endpoint():
        return JSONResponse(
            content={"data": "test"},
            headers={"X-Custom-Header": "custom-value"},
        )

    async with AsyncClient(
        transport=ASGITransport(app=app_with_middleware), base_url="http://test"
    ) as client:
        response = await client.get("/api/with-headers")

    assert response.status_code == 200
    assert response.headers.get("X-Custom-Header") == "custom-value"


def test_should_skip_non_json():
    """Test middleware skips non-JSON responses."""
    middleware = ResponseWrapperMiddleware(app=MagicMock())
    request = MagicMock(spec=Request)
    request.url.path = "/test"

    response = PlainTextResponse("plain text")
    response.headers["content-type"] = "text/plain"

    assert middleware._should_skip(request, response) is True


def test_should_skip_docs_paths():
    """Test middleware skips documentation paths."""
    middleware = ResponseWrapperMiddleware(app=MagicMock())
    request = MagicMock(spec=Request)
    response = MagicMock(spec=JSONResponse)
    response.headers.get = MagicMock(return_value="application/json")

    docs_paths = [
        "/docs",
        "/redoc",
        "/docs/oauth2-redirect",
        "/openapi.json",
    ]

    for path in docs_paths:
        request.url.path = path
        assert middleware._should_skip(request, response) is True, f"Should skip {path}"


def test_should_not_skip_api_paths():
    """Test middleware does not skip API paths."""
    middleware = ResponseWrapperMiddleware(app=MagicMock())
    request = MagicMock(spec=Request)
    request.url.path = "/api/users"
    response = MagicMock(spec=JSONResponse)
    response.headers.get = MagicMock(return_value="application/json")

    assert middleware._should_skip(request, response) is False


def test_is_already_wrapped_with_valid_response():
    """Test detection of already wrapped response."""
    middleware = ResponseWrapperMiddleware(app=MagicMock())

    valid_wrapped = {
        "code": 200,
        "msg": "success",
        "data": {"key": "value"},
    }

    assert middleware._is_already_wrapped(valid_wrapped) is True


def test_is_already_wrapped_with_invalid_response():
    """Test detection of invalid wrapped response."""
    middleware = ResponseWrapperMiddleware(app=MagicMock())

    invalid_responses = [
        {"code": 200, "msg": "success"},  # Missing data field
        {"not_wrapped": "response"},  # Different structure
        "string response",  # Not a dict
        None,  # None response
    ]

    for invalid in invalid_responses:
        assert middleware._is_already_wrapped(invalid) is False
