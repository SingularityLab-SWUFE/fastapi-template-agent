import pytest
from typing import List
from src.core.responses.schemas import (
    SuccessResponse,
    ErrorResponse,
    PaginatedResponse,
    PaginationInfo
)
from src.core.schemas.user import User

@pytest.mark.asyncio
async def test_success_response_creation():
    data = {"name": "test", "value": 123}
    response = SuccessResponse.success(data, "Operation successful")

    assert response.code == 200
    assert response.msg == "Operation successful"
    assert response.data == data

@pytest.mark.asyncio
async def test_success_response_default_message():
    data = {"id": 1}
    response = SuccessResponse.success(data)

    assert response.code == 200
    assert response.msg == "Success"
    assert response.data == data

@pytest.mark.asyncio
async def test_error_response_creation():
    response = ErrorResponse.error(404, "Not found")

    assert response.code == 404
    assert response.msg == "Not found"
    assert response.data is None

@pytest.mark.asyncio
async def test_pagination_info():
    pagination = PaginationInfo(
        page=1,
        page_size=20,
        total=100,
        total_pages=5
    )

    assert pagination.page == 1
    assert pagination.page_size == 20
    assert pagination.total == 100
    assert pagination.total_pages == 5

@pytest.mark.asyncio
async def test_paginated_response():
    users = [
        User(username="user1", hashed_password="hash1"),
        User(username="user2", hashed_password="hash2")
    ]

    pagination = PaginationInfo(
        page=1,
        page_size=20,
        total=100,
        total_pages=5
    )

    response = PaginatedResponse(
        code=200,
        msg="Success",
        data=users,
        pagination=pagination
    )

    assert response.code == 200
    assert response.msg == "Success"
    assert response.data == users
    assert response.pagination == pagination

@pytest.mark.asyncio
async def test_success_response_with_user():
    user = User(username="testuser", hashed_password="hash")
    response = SuccessResponse.success(user, "User retrieved")

    assert response.code == 200
    assert response.msg == "User retrieved"
    assert response.data == user
    assert response.data.username == "testuser"

@pytest.mark.asyncio
async def test_success_response_with_list():
    users = [
        User(username="user1", hashed_password="hash1"),
        User(username="user2", hashed_password="hash2"),
        User(username="user3", hashed_password="hash3")
    ]

    response = SuccessResponse.success(users, "Users retrieved")

    assert response.code == 200
    assert response.msg == "Users retrieved"
    assert len(response.data) == 3
    assert response.data[0].username == "user1"
