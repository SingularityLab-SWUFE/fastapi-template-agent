import pytest

from src.core.responses.schemas import JsonResponse


def test_success_response_creates_json_response():
    data = {"result": "success"}
    response = JsonResponse.success(data)

    assert isinstance(response, JsonResponse)
    assert response.success is True
    assert response.code == 200
    assert response.data == data
    assert response.error is None


def test_success_response_with_various_types():
    test_cases = [
        {"key": "value"},
        "string",
        [1, 2, 3],
        42,
        None,
        {"nested": {"data": "value"}},
    ]

    for data in test_cases:
        response = JsonResponse.success(data)
        assert response.data == data
        assert response.success is True
        assert response.code == 200


def test_error_response_creates_json_response():
    response = JsonResponse.error(40001, "Bad request")

    assert isinstance(response, JsonResponse)
    assert response.success is False
    assert response.code == 40001
    assert response.data is None
    assert response.error == {"code": 40001, "msg": "Bad request"}


@pytest.mark.parametrize(
    "code,msg",
    [
        (10001, "Error message"),
        (40001, "Bad request"),
        (40404, "Not found"),
        (50000, "Internal error"),
        (99999, "Maximum error code"),
    ],
)
def test_error_response_with_params(code, msg):
    response = JsonResponse.error(code, msg)

    assert response.success is False
    assert response.code == code
    assert response.error == {"code": code, "msg": msg}


def test_error_response_with_special_characters():
    special_msg = "Error: @#$%^&*()[]{}|\\:;\"'<>?,./"
    response = JsonResponse.error(50001, special_msg)

    assert response.error == {"code": 50001, "msg": special_msg}


def test_success_response_empty_data():
    response = JsonResponse.success(None)

    assert response.success is True
    assert response.code == 200
    assert response.data is None
    assert response.error is None


def test_error_response_empty_message():
    response = JsonResponse.error(40001, "")

    assert response.success is False
    assert response.code == 40001
    assert response.error == {"code": 40001, "msg": ""}


def test_success_response_with_nested_data():
    nested_data = {
        "users": [{"id": i, "name": f"user{i}"} for i in range(5)],
        "metadata": {"total": 5, "page": 1},
    }
    response = JsonResponse.success(nested_data)

    assert response.data == nested_data
    assert response.success is True


def test_error_response_preserves_error_code():
    code = 10001
    msg = "Test error"
    response = JsonResponse.error(code, msg)

    assert response.code == code
    assert response.error["code"] == code
