import pytest
from unittest.mock import Mock
from fastapi import Request
from src.core.decorators.response import handle_response, handle_request
from src.core.responses.schemas import SuccessResponse
from src.core.schemas.user import User

@pytest.mark.asyncio
async def test_handle_response_decorator():
    test_data = {"message": "Hello World"}

    @handle_response
    async def test_function():
        return test_data

    result = await test_function()

    assert isinstance(result, dict)
    assert result["code"] == 200
    assert result["msg"] == "Success"
    assert result["data"] == test_data

@pytest.mark.asyncio
async def test_handle_response_with_custom_message():
    test_data = {"id": 123}

    @handle_response
    async def test_function():
        return test_data

    result = await test_function()

    assert result["msg"] == "Success"

@pytest.mark.asyncio
async def test_handle_request_decorator():
    test_data = {"status": "active"}
    mock_request = Mock(spec=Request)

    @handle_request
    async def test_function(request: Request):
        assert request == mock_request
        return test_data

    result = await test_function(mock_request)

    assert isinstance(result, dict)
    assert result["code"] == 200
    assert result["msg"] == "Success"
    assert result["data"] == test_data

@pytest.mark.asyncio
async def test_handle_request_with_user():
    user = User(username="testuser", hashed_password="hash123")
    mock_request = Mock(spec=Request)

    @handle_request
    async def test_function(request: Request) -> User:
        return user

    result = await test_function(mock_request)

    assert isinstance(result, dict)
    assert result["data"]["username"] == "testuser"

@pytest.mark.asyncio
async def test_handle_request_with_list():
    users = [
        User(username="user1", hashed_password="hash1"),
        User(username="user2", hashed_password="hash2")
    ]
    mock_request = Mock(spec=Request)

    @handle_request
    async def test_function(request: Request):
        return users

    result = await test_function(mock_request)

    assert isinstance(result, dict)
    assert len(result["data"]) == 2
    assert result["data"][0]["username"] == "user1"
    assert result["data"][1]["username"] == "user2"

@pytest.mark.asyncio
async def test_handle_response_exception_passthrough():
    test_error = ValueError("Test error")

    @handle_response
    async def test_function():
        raise test_error

    with pytest.raises(ValueError) as exc_info:
        await test_function()

    assert str(exc_info.value) == "Test error"

@pytest.mark.asyncio
async def test_handle_request_exception_passthrough():
    test_error = RuntimeError("Unexpected error")
    mock_request = Mock(spec=Request)

    @handle_request
    async def test_function(request: Request):
        raise test_error

    with pytest.raises(RuntimeError) as exc_info:
        await test_function(mock_request)

    assert str(exc_info.value) == "Unexpected error"

@pytest.mark.asyncio
async def test_decorator_preserves_function_name():
    @handle_response
    async def my_custom_function():
        return {"data": "test"}

    assert my_custom_function.__name__ == "my_custom_function"

@pytest.mark.asyncio
async def test_handle_request_with_args_and_kwargs():
    mock_request = Mock(spec=Request)

    @handle_request
    async def test_function(request: Request, value: int, text: str = "default"):
        return {"value": value, "text": text}

    result = await test_function(mock_request, 42, text="custom")

    assert isinstance(result, dict)
    assert result["data"]["value"] == 42
    assert result["data"]["text"] == "custom"
