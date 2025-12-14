from src.core.schemas.error import ErrorCode
from src.exceptions import BusinessException, InvalidPasswordException


def test_business_exception_with_error_code():
    exc = BusinessException(ErrorCode.AUTH_INVALID_CREDENTIALS, "Invalid credentials")

    assert exc.code == ErrorCode.AUTH_INVALID_CREDENTIALS
    assert exc.msg == "Invalid credentials"
    assert exc.data is None
    assert str(exc) == "[10001] Invalid credentials"


def test_business_exception_with_data():
    exc = BusinessException(
        ErrorCode.BIZ_INSUFFICIENT_BALANCE,
        "Insufficient balance",
        data={"balance": 100, "required": 200},
    )

    assert exc.code == ErrorCode.BIZ_INSUFFICIENT_BALANCE
    assert exc.msg == "Insufficient balance"
    assert exc.data == {"balance": 100, "required": 200}
    assert str(exc) == "[50001] Insufficient balance"


def test_business_exception_different_error_codes():
    exc1 = BusinessException(ErrorCode.USER_NOT_FOUND, "User not found")
    exc2 = BusinessException(ErrorCode.PERM_INSUFFICIENT, "Permission denied")

    assert exc1.code == ErrorCode.USER_NOT_FOUND
    assert exc2.code == ErrorCode.PERM_INSUFFICIENT
    assert str(exc1) == "[20001] User not found"
    assert str(exc2) == "[30001] Permission denied"


def test_domain_exception():
    exc = InvalidPasswordException(remaining_attempts=3)

    assert exc.code == ErrorCode.AUTH_INVALID_PASSWORD
    assert exc.msg == "Invalid password, 3 attempts remaining"
    assert exc.data == {"remaining_attempts": 3}
    assert str(exc) == "[10002] Invalid password, 3 attempts remaining"
