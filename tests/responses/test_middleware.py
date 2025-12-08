"""Test unified response middleware."""

from unittest.mock import MagicMock


def test_should_skip_non_json():
    """Test middleware skips non-JSON responses."""
    from src.responses.middleware import ResponseWrapperMiddleware
    from fastapi import Request
    from fastapi.responses import PlainTextResponse

    middleware = ResponseWrapperMiddleware(app=MagicMock())
    request = MagicMock(spec=Request)
    request.url.path = "/test"

    response = PlainTextResponse("plain text")
    response.headers["content-type"] = "text/plain"

    assert middleware._should_skip(request, response) is True


def test_should_skip_docs_paths():
    """Test middleware skips documentation paths."""
    from src.responses.middleware import ResponseWrapperMiddleware
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from unittest.mock import MagicMock

    middleware = ResponseWrapperMiddleware(app=MagicMock())
    request = MagicMock(spec=Request)
    response = MagicMock(spec=JSONResponse)
    response.headers.get = MagicMock(return_value="application/json")

    docs_paths = [
        "/docs",
        "/redoc",
        "/docs/oauth2-redirect",
        "/openapi.json",
    ]

    for path in docs_paths:
        request.url.path = path
        assert middleware._should_skip(request, response) is True, f"Should skip {path}"


def test_should_not_skip_api_paths():
    """Test middleware does not skip API paths."""
    from src.responses.middleware import ResponseWrapperMiddleware
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from unittest.mock import MagicMock

    middleware = ResponseWrapperMiddleware(app=MagicMock())
    request = MagicMock(spec=Request)
    request.url.path = "/api/users"
    response = MagicMock(spec=JSONResponse)
    response.headers.get = MagicMock(return_value="application/json")

    assert middleware._should_skip(request, response) is False


def test_is_already_unified_with_valid_response():
    """Test detection of already unified response."""
    from src.responses.middleware import ResponseWrapperMiddleware

    middleware = ResponseWrapperMiddleware(app=MagicMock())

    valid_unified = {
        "code": 200,
        "msg": "success",
        "data": {"key": "value"},
        "is_success": True,
    }

    assert middleware._is_already_unified(valid_unified) is True


def test_is_already_unified_with_invalid_response():
    """Test detection of invalid unified response."""
    from src.responses.middleware import ResponseWrapperMiddleware

    middleware = ResponseWrapperMiddleware(app=MagicMock())

    invalid_responses = [
        {"code": 200, "msg": "success"},  # Missing fields
        {"code": 200, "msg": "success", "data": {}},  # Missing is_success field
        {"code": 200, "msg": "success", "data": {}, "is_success": "true"},  # Wrong type
        {"not_unified": "response"},  # Different structure
        "string response",  # Not a dict
        None,  # None response
    ]

    for invalid in invalid_responses:
        assert middleware._is_already_unified(invalid) is False, f"Should reject: {invalid}"


def test_extract_error_msg_from_dict_with_detail():
    """Test error message extraction from dict with 'detail' field."""
    from src.responses.middleware import ResponseWrapperMiddleware

    middleware = ResponseWrapperMiddleware(app=MagicMock())

    payload = {"detail": "Error details"}
    assert middleware._extract_error_msg(payload) == "Error details"


def test_extract_error_msg_from_dict_with_msg():
    """Test error message extraction from dict with 'msg' field."""
    from src.responses.middleware import ResponseWrapperMiddleware

    middleware = ResponseWrapperMiddleware(app=MagicMock())

    payload = {"msg": "Custom message"}
    assert middleware._extract_error_msg(payload) == "Custom message"


def test_extract_error_msg_from_dict_with_message():
    """Test error message extraction from dict with 'message' field."""
    from src.responses.middleware import ResponseWrapperMiddleware

    middleware = ResponseWrapperMiddleware(app=MagicMock())

    payload = {"message": "Error message"}
    assert middleware._extract_error_msg(payload) == "Error message"


def test_extract_error_msg_from_dict_with_nested_detail():
    """Test error message extraction from dict with nested detail."""
    from src.responses.middleware import ResponseWrapperMiddleware

    middleware = ResponseWrapperMiddleware(app=MagicMock())

    payload = {"detail": {"error": "Something went wrong", "code": 123}}
    result = middleware._extract_error_msg(payload)
    assert "error" in result
    assert "code" in result


def test_extract_error_msg_from_string():
    """Test error message extraction from string payload."""
    from src.responses.middleware import ResponseWrapperMiddleware

    middleware = ResponseWrapperMiddleware(app=MagicMock())

    assert middleware._extract_error_msg("String error") == "String error"


def test_extract_error_msg_from_list():
    """Test error message extraction from list payload."""
    from src.responses.middleware import ResponseWrapperMiddleware
    import json

    middleware = ResponseWrapperMiddleware(app=MagicMock())

    payload = ["error1", "error2", "error3"]
    result = middleware._extract_error_msg(payload)
    assert json.loads(result) == payload


def test_extract_error_msg_from_none():
    """Test error message extraction from None payload."""
    from src.responses.middleware import ResponseWrapperMiddleware

    middleware = ResponseWrapperMiddleware(app=MagicMock())

    assert middleware._extract_error_msg(None) == "error"


def test_extract_error_msg_from_unknown_type():
    """Test error message extraction from unknown payload type."""
    from src.responses.middleware import ResponseWrapperMiddleware

    middleware = ResponseWrapperMiddleware(app=MagicMock())

    assert middleware._extract_error_msg(123) == "error"
