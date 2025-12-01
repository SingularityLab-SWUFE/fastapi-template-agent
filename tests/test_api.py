import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_list_users_success():
    response = client.get("/api/v1/users?page=1&page_size=20")
    assert response.status_code == 200

    data = response.json()
    assert "code" in data
    assert "msg" in data
    assert "data" in data
    assert "pagination" in data

    assert data["code"] == 200
    assert data["msg"] == "Success"
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 20
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 20

@pytest.mark.asyncio
async def test_list_users_with_pagination():
    response = client.get("/api/v1/users?page=2&page_size=10")
    assert response.status_code == 200

    data = response.json()
    assert data["pagination"]["page"] == 2
    assert data["pagination"]["page_size"] == 10
    assert len(data["data"]) == 10

@pytest.mark.asyncio
async def test_get_user_success():
    response = client.get("/api/v1/users/5")
    assert response.status_code == 200

    data = response.json()
    assert "code" in data
    assert "msg" in data
    assert "data" in data

    assert data["code"] == 200
    assert data["msg"] == "Success"
    assert data["data"]["username"] == "user5"

@pytest.mark.asyncio
async def test_get_user_not_found():
    response = client.get("/api/v1/users/999")
    assert response.status_code == 404

    data = response.json()
    assert data["code"] == 404
    assert "User not found" in data["msg"]

@pytest.mark.asyncio
async def test_get_user_invalid_id():
    response = client.get("/api/v1/users/0")
    assert response.status_code == 400

    data = response.json()
    assert data["code"] == 400
    assert "Invalid user ID" in data["msg"]

@pytest.mark.asyncio
async def test_get_user_negative_id():
    response = client.get("/api/v1/users/-1")
    assert response.status_code == 400

    data = response.json()
    assert data["code"] == 400
    assert "Invalid user ID" in data["msg"]

@pytest.mark.asyncio
async def test_create_user():
    user_data = {
        "username": "newuser",
        "hashed_password": "newpasswordhash"
    }

    response = client.post("/api/v1/users", json=user_data)
    assert response.status_code == 200

    data = response.json()
    assert data["code"] == 200
    assert data["msg"] == "Success"
    assert data["data"]["username"] == "newuser"
    assert data["data"]["hashed_password"] == "newpasswordhash"

@pytest.mark.asyncio
async def test_create_user_with_id():
    user_data = {
        "id": 100,
        "username": "user_with_id",
        "hashed_password": "hash123"
    }

    response = client.post("/api/v1/users", json=user_data)
    assert response.status_code == 200

    data = response.json()
    assert data["data"]["username"] == "user_with_id"

@pytest.mark.asyncio
async def test_response_structure_success():
    response = client.get("/api/v1/users/1")
    assert response.status_code == 200

    data = response.json()
    assert set(data.keys()) == {"code", "msg", "data"}

@pytest.mark.asyncio
async def test_response_structure_error():
    response = client.get("/api/v1/users/abc")
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_pagination_structure():
    response = client.get("/api/v1/users?page=1&page_size=15")
    assert response.status_code == 200

    data = response.json()
    pagination = data["pagination"]
    assert set(pagination.keys()) == {"page", "page_size", "total", "total_pages"}
    assert pagination["page"] == 1
    assert pagination["page_size"] == 15

@pytest.mark.asyncio
async def test_user_data_structure():
    response = client.get("/api/v1/users/1")
    assert response.status_code == 200

    data = response.json()
    user = data["data"]
    assert "username" in user
    assert "hashed_password" in user
