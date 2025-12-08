from src.exceptions import BusinessException


def test_business_exception_defaults():
    exc = BusinessException()

    assert exc.code == 400
    assert exc.msg == "Business error"
    assert str(exc) == "[400] Business error"


def test_business_exception_custom_values():
    exc = BusinessException(code=422, msg="Invalid input")

    assert exc.code == 422
    assert exc.msg == "Invalid input"
    assert str(exc) == "[422] Invalid input"
