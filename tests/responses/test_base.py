import pytest


@pytest.mark.parametrize(
    "factory_kwargs,expected_code,expected_msg,expected_data",
    [
        (
            {"data": {"key": "value"}, "msg": "Success!", "code": 200},
            200,
            "Success!",
            {"key": "value"},
        ),
        ({}, 200, "success", None),
        ({"code": 201, "msg": "Created"}, 201, "Created", None),
    ],
)
def test_response_success_factory_sets_fields(
    factory_kwargs, expected_code, expected_msg, expected_data
):
    from src.responses.base import Response

    response = Response.success(**factory_kwargs)

    assert response.code == expected_code
    assert response.msg == expected_msg
    assert response.data == expected_data


@pytest.mark.parametrize(
    "factory_kwargs,expected_code,expected_msg,expected_data",
    [
        (
            {"code": 400, "msg": "Bad request", "data": {"error": "detail"}},
            400,
            "Bad request",
            {"error": "detail"},
        ),
        (
            {"code": 500, "msg": "Internal server error"},
            500,
            "Internal server error",
            None,
        ),
    ],
)
def test_response_error_factory_sets_fields(
    factory_kwargs, expected_code, expected_msg, expected_data
):
    from src.responses.base import Response

    response = Response.error(**factory_kwargs)

    assert response.code == expected_code
    assert response.msg == expected_msg
    assert response.data == expected_data


def test_response_model_dump():
    """Test Response.model_dump() returns correct dictionary."""
    from src.responses.base import Response

    response = Response.success(data={"test": "data"}, msg="OK", code=200)
    dumped = response.model_dump()

    assert dumped == {
        "code": 200,
        "msg": "OK",
        "data": {"test": "data"},
    }


def test_response_generic_types():
    """Test Response with different generic types."""
    from src.responses.base import Response

    response_str = Response.success(data="string data")
    assert response_str.data == "string data"

    response_int = Response.success(data=42)
    assert response_int.data == 42

    response_list = Response.success(data=[1, 2, 3])
    assert response_list.data == [1, 2, 3]

    response_dict = Response.success(data={"nested": {"key": "value"}})
    assert response_dict.data == {"nested": {"key": "value"}}


def test_response_with_none_data():
    """Test Response when data is explicitly None."""
    from src.responses.base import Response

    response = Response.success(data=None)
    assert response.data is None

    response_error = Response.error(code=404, msg="Not found", data=None)
    assert response_error.data is None
