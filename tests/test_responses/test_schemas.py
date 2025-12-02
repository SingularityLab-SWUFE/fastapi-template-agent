import pytest
from pydantic import ValidationError

from src.responses import JsonResponse


@pytest.mark.parametrize(
    "data,expected_data",
    [
        ({"key": "value"}, {"key": "value"}),
        ("simple string", "simple string"),
        ([1, 2, 3], [1, 2, 3]),
        (42, 42),
        (None, None),
        ({"nested": {"data": "value"}}, {"nested": {"data": "value"}}),
    ],
)
def test_json_response_success(data, expected_data):
    response = JsonResponse.success(data)

    assert response.success is True
    assert response.code == 200
    assert response.data == expected_data
    assert response.error is None


def test_json_response_success_with_dict():
    data = {"user_id": 1, "username": "test"}
    response = JsonResponse.success(data)

    assert response.success is True
    assert response.code == 200
    assert response.data == data
    assert response.error is None


def test_json_response_success_with_list():
    data = [{"id": 1}, {"id": 2}]
    response = JsonResponse.success(data)

    assert response.success is True
    assert response.code == 200
    assert response.data == data
    assert response.error is None


@pytest.mark.parametrize(
    "code,msg,expected_code,expected_msg",
    [
        (10001, "Error message", 10001, "Error message"),
        (40001, "Bad request", 40001, "Bad request"),
        (40404, "Not found", 40404, "Not found"),
        (50000, "Internal error", 50000, "Internal error"),
    ],
)
def test_json_response_error(code, msg, expected_code, expected_msg):
    response = JsonResponse.error(code, msg)

    assert response.success is False
    assert response.code == expected_code
    assert response.data is None
    assert response.error == {"code": expected_code, "msg": expected_msg}


def test_json_response_error_preserves_message():
    msg = "Custom error with special chars: @#$%"
    response = JsonResponse.error(40001, msg)

    assert response.error == {"code": 40001, "msg": msg}


def test_json_response_error_code_validation_min():
    with pytest.raises(ValueError, match="Error code must be between 10000 and 99999"):
        JsonResponse.error(9999, "Too low")


def test_json_response_error_code_validation_max():
    with pytest.raises(ValueError, match="Error code must be between 10000 and 99999"):
        JsonResponse.error(100000, "Too high")


def test_json_response_error_code_boundary_valid():
    response = JsonResponse.error(10000, "Minimum valid")
    assert response.error == {"code": 10000, "msg": "Minimum valid"}


def test_json_response_error_code_boundary_max_valid():
    response = JsonResponse.error(99999, "Maximum valid")
    assert response.error == {"code": 99999, "msg": "Maximum valid"}


def test_json_response_model_dump_success():
    data = {"result": "success"}
    response = JsonResponse.success(data)
    dumped = response.model_dump()

    assert dumped == {
        "success": True,
        "code": 200,
        "data": data,
        "error": None,
    }


def test_json_response_model_dump_error():
    response = JsonResponse.error(40001, "Bad request")
    dumped = response.model_dump()

    assert dumped == {
        "success": False,
        "code": 40001,
        "data": None,
        "error": {"code": 40001, "msg": "Bad request"},
    }


def test_json_response_with_complex_nested_data():
    complex_data = {
        "user": {"id": 1, "profile": {"name": "John", "settings": {"theme": "dark"}}},
        "items": [{"id": i, "name": f"item{i}"} for i in range(3)],
    }
    response = JsonResponse.success(complex_data)

    assert response.success is True
    assert response.data == complex_data


def test_json_response_with_empty_string():
    response = JsonResponse.success("")

    assert response.success is True
    assert response.data == ""


def test_json_response_with_empty_dict():
    response = JsonResponse.success({})

    assert response.success is True
    assert response.data == {}


def test_json_response_with_empty_list():
    response = JsonResponse.success([])

    assert response.success is True
    assert response.data == []


def test_json_response_generic_type_preservation():
    from typing import TypedDict

    class UserData(TypedDict):
        id: int
        name: str

    user_data: UserData = {"id": 1, "name": "test"}
    response = JsonResponse.success(user_data)

    assert response.success is True
    assert response.data == user_data
