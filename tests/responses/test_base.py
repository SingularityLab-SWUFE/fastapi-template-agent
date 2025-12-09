"""Test unified response model."""


def test_response_success_with_data():
    """Test Response.success() factory method with data."""
    from src.responses.base import Response

    response = Response.success(data={"key": "value"}, msg="Success!", code=200)

    assert response.code == 200
    assert response.msg == "Success!"
    assert response.data == {"key": "value"}


def test_response_success_without_data():
    """Test Response.success() factory method without data."""
    from src.responses.base import Response

    response = Response.success()

    assert response.code == 200
    assert response.msg == "success"
    assert response.data is None


def test_response_success_with_custom_code():
    """Test Response.success() factory method with custom status code."""
    from src.responses.base import Response

    response = Response.success(code=201, msg="Created")

    assert response.code == 201
    assert response.msg == "Created"
    assert response.data is None


def test_response_error():
    """Test Response.error() factory method."""
    from src.responses.base import Response

    response = Response.error(code=400, msg="Bad request", data={"error": "detail"})

    assert response.code == 400
    assert response.msg == "Bad request"
    assert response.data == {"error": "detail"}


def test_response_error_minimal():
    """Test Response.error() factory method with minimal params."""
    from src.responses.base import Response

    response = Response.error(code=500, msg="Internal server error")

    assert response.code == 500
    assert response.msg == "Internal server error"
    assert response.data is None


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
