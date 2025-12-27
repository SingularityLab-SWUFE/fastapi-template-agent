import pytest
from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from httpx import AsyncClient, ASGITransport

from src.shared.errors import ErrorCode
from src.exceptions import BusinessException
from src.handlers import register_exception_handlers


def test_register_all_handlers(base_app: FastAPI):
    register_exception_handlers(base_app)

    assert Exception in base_app.exception_handlers

    handler = base_app.exception_handlers[Exception]
    assert callable(handler)


@pytest.mark.parametrize(
    "code,msg,expected_status,expected_body_subset,raise_app_exceptions",
    [
        (
            ErrorCode.AUTH_ACCOUNT_LOCKED,
            "I'm a teapot",
            403,
            {"code": ErrorCode.AUTH_ACCOUNT_LOCKED, "msg": "I'm a teapot"},
            True,
        ),
        (
            ErrorCode.DATA_VALIDATION_FAILED,
            "Validation failed",
            422,
            {"code": ErrorCode.DATA_VALIDATION_FAILED, "data": {"field": "email"}},
            True,
        ),
        (
            ErrorCode.SYS_INTERNAL_ERROR,
            "Internal error",
            500,
            {"code": ErrorCode.SYS_INTERNAL_ERROR, "msg": "Internal error"},
            False,
        ),
    ],
)
@pytest.mark.asyncio
async def test_handler_returns_unified_response_for_business_exception(
    full_app: FastAPI,
    code,
    msg,
    expected_status,
    expected_body_subset,
    raise_app_exceptions,
):
    @full_app.get("/test")
    async def test_endpoint():
        if code == ErrorCode.DATA_VALIDATION_FAILED:
            raise BusinessException(code, msg, data={"field": "email"})
        raise BusinessException(code, msg)

    transport = ASGITransport(app=full_app, raise_app_exceptions=raise_app_exceptions)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test")

    assert response.status_code == expected_status
    body = response.json()
    for k, v in expected_body_subset.items():
        assert body[k] == v


@pytest.mark.parametrize(
    "status_code,detail,expected_msg,raise_app_exceptions",
    [
        (404, "Resource not found", "Resource not found", True),
        (400, {"msg": "Bad request", "field": "email"}, "Bad request", True),
        (422, ["Email is required", "Password is required"], "Email is required", True),
        (500, None, "Internal Server Error", False),
    ],
)
@pytest.mark.asyncio
async def test_handler_returns_unified_response_for_http_exception(
    full_app: FastAPI,
    status_code,
    detail,
    expected_msg,
    raise_app_exceptions,
):
    @full_app.get("/test")
    async def test_endpoint():
        raise HTTPException(status_code=status_code, detail=detail)

    transport = ASGITransport(app=full_app, raise_app_exceptions=raise_app_exceptions)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test")

    assert response.status_code == status_code
    body = response.json()
    assert body["msg"] == expected_msg

    if status_code == 404:
        assert body["code"] == 404


@pytest.mark.parametrize(
    "errors,expected_validation_errors_len,expected_first_field",
    [
        (
            [
                {
                    "loc": ["body", "email"],
                    "msg": "Invalid email",
                    "type": "value_error",
                }
            ],
            1,
            "email",
        ),
        (
            [
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
            ],
            2,
            "email",
        ),
        (
            [
                {
                    "loc": ["body", "user", "email"],
                    "msg": "Invalid email",
                    "type": "value_error",
                }
            ],
            1,
            "user.email",
        ),
    ],
)
@pytest.mark.asyncio
async def test_handler_returns_unified_response_for_request_validation_error(
    full_app: FastAPI,
    errors,
    expected_validation_errors_len,
    expected_first_field,
):
    @full_app.get("/test")
    async def test_endpoint():
        raise RequestValidationError(errors=errors)

    async with AsyncClient(
        transport=ASGITransport(app=full_app), base_url="http://test"
    ) as client:
        response = await client.get("/test")

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == 422
    assert body["msg"] == "Validation failed"

    validation_errors = body["data"]["validation_errors"]
    assert len(validation_errors) == expected_validation_errors_len
    assert validation_errors[0]["field"] == expected_first_field


@pytest.mark.asyncio
async def test_handler_returns_unified_response_for_unhandled_exception(
    full_app: FastAPI,
):
    @full_app.get("/test")
    async def test_endpoint():
        raise RuntimeError("Unexpected error")

    transport = ASGITransport(app=full_app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test")

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == 500
    assert body["msg"] == "Internal server error"
    assert body["data"]["error_type"] == "RuntimeError"
