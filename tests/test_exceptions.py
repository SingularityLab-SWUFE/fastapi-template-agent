from src.exceptions import BusinessException


def test_business_exception_defaults():
    exc = BusinessException()

    assert exc.http_code == 400
    assert exc.business_code == 400
    assert exc.msg == "Business error"
    assert str(exc) == "[400] Business error"


def test_business_exception_custom_values():
    exc = BusinessException(http_code=422, business_code=422, msg="Invalid input")

    assert exc.http_code == 422
    assert exc.business_code == 422
    assert exc.msg == "Invalid input"
    assert str(exc) == "[422] Invalid input"


def test_business_exception_with_different_codes():
    exc = BusinessException(http_code=400, business_code=1001, msg="Business rule violated")

    assert exc.http_code == 400
    assert exc.business_code == 1001
    assert exc.msg == "Business rule violated"
    assert str(exc) == "[1001] Business rule violated"


def test_business_exception_defaults_business_code_to_http_code():
    exc = BusinessException(http_code=403)

    assert exc.http_code == 403
    assert exc.business_code == 403
    assert exc.msg == "Business error"
