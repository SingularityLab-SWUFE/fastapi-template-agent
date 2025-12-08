import json

from fastapi import FastAPI
from starlette.requests import Request

from src.exception_handlers import register_business_exception_handler
from src.exceptions import BusinessException


async def test_business_exception_handler_uses_provided_status():
    app = FastAPI()
    register_business_exception_handler(app)
    handler = app.exception_handlers[BusinessException]

    request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
    response = await handler(request, BusinessException(code=422, msg="Invalid input"))

    assert response.status_code == 422
    body = json.loads(response.body)
    assert body["code"] == 422
    assert body["msg"] == "Invalid input"
    assert body["detail"] == "Invalid input"


async def test_business_exception_handler_defaults_status_for_invalid_code():
    app = FastAPI()
    register_business_exception_handler(app)
    handler = app.exception_handlers[BusinessException]

    request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
    response = await handler(request, BusinessException(code=9999, msg="Out of range"))

    assert response.status_code == 400
    body = json.loads(response.body)
    assert body["code"] == 9999
    assert body["msg"] == "Out of range"
