import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from src.core.handlers.exceptions import (
    BaseExceptionHandler,
    HTTPExceptionHandler,
    ValueErrorHandler,
    BusinessExceptionHandler,
    BusinessException
)

@pytest.mark.asyncio
async def test_http_exception_handler():
    handler = HTTPExceptionHandler()
    request = Mock(spec=Request)
    exc = HTTPException(status_code=404, detail="Not found")

    result = await handler.handle(request, exc)

    assert isinstance(result, JSONResponse)
    assert result.status_code == 404
    content = result.body.decode()
    assert '"code":404' in content
    assert '"msg":"Not found"' in content

@pytest.mark.asyncio
async def test_value_error_handler():
    handler = ValueErrorHandler()
    request = Mock(spec=Request)
    exc = ValueError("Invalid value")

    result = await handler.handle(request, exc)

    assert isinstance(result, JSONResponse)
    assert result.status_code == 400
    content = result.body.decode()
    assert '"code":400' in content
    assert '"msg":"Invalid value"' in content

@pytest.mark.asyncio
async def test_business_exception_handler():
    handler = BusinessExceptionHandler()
    request = Mock(spec=Request)
    exc = BusinessException(code=1001, message="Business rule violation")

    result = await handler.handle(request, exc)

    assert isinstance(result, JSONResponse)
    assert result.status_code == 200
    content = result.body.decode()
    assert '"code":1001' in content
    assert '"msg":"Business rule violation"' in content

@pytest.mark.asyncio
async def test_exception_handler_chain():
    chain = HTTPExceptionHandler(
        ValueErrorHandler(
            BusinessExceptionHandler()
        )
    )

    request = Mock(spec=Request)

    http_exc = HTTPException(status_code=403, detail="Forbidden")
    result = await chain.handle(request, http_exc)
    assert result.status_code == 403

    value_exc = ValueError("Bad request")
    result = await chain.handle(request, value_exc)
    assert result.status_code == 400

    biz_exc = BusinessException(code=1002, message="Custom error")
    result = await chain.handle(request, biz_exc)
    assert result.status_code == 200

@pytest.mark.asyncio
async def test_default_exception_handling():
    handler = ValueErrorHandler()
    request = Mock(spec=Request)
    exc = RuntimeError("Unexpected error")

    result = await handler.handle(request, exc)

    assert isinstance(result, JSONResponse)
    assert result.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    content = result.body.decode()
    assert '"code":500' in content

@pytest.mark.asyncio
async def test_business_exception_properties():
    exc = BusinessException(code=5001, message="Custom business error")

    assert exc.code == 5001
    assert exc.message == "Custom business error"
    assert str(exc) == "Custom business error"

@pytest.mark.asyncio
async def test_http_exception_handler_does_not_handle_value_error():
    handler = HTTPExceptionHandler()
    request = Mock(spec=Request)
    exc = ValueError("Test error")

    result = await handler.handle(request, exc)

    assert isinstance(result, JSONResponse)
    assert result.status_code == HTTP_500_INTERNAL_SERVER_ERROR

@pytest.mark.asyncio
async def test_value_error_handler_does_not_handle_http_exception():
    handler = ValueErrorHandler()
    request = Mock(spec=Request)
    exc = HTTPException(status_code=404, detail="Not found")

    result = await handler.handle(request, exc)

    assert isinstance(result, JSONResponse)
    assert result.status_code == HTTP_500_INTERNAL_SERVER_ERROR
