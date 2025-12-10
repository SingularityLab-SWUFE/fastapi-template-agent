from src.exceptions import BusinessException


def test_business_exception_required_params():
    exc = BusinessException(business_code=400, msg="Business error")

    assert exc.business_code == 400
    assert exc.msg == "Business error"
    assert exc.data is None
    assert str(exc) == "[400] Business error"


def test_business_exception_custom_values():
    exc = BusinessException(business_code=422, msg="Invalid input", data={"field": "email"})

    assert exc.business_code == 422
    assert exc.msg == "Invalid input"
    assert exc.data == {"field": "email"}
    assert str(exc) == "[422] Invalid input"


def test_business_exception_with_different_codes():
    exc = BusinessException(business_code=1001, msg="Business rule violated")

    assert exc.business_code == 1001
    assert exc.msg == "Business rule violated"
    assert str(exc) == "[1001] Business rule violated"


def test_business_exception_with_additional_data():
    exc = BusinessException(
        business_code=400,
        msg="Validation failed",
        data={"errors": ["Email required", "Password too short"]}
    )

    assert exc.business_code == 400
    assert exc.msg == "Validation failed"
    assert exc.data == {"errors": ["Email required", "Password too short"]}
