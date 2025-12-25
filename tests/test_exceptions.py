import pytest

from src.shared.errors import ErrorCode
from src.exceptions import (
    BusinessException,
    InsufficientPermissionException,
    InsufficientRoleException,
    InvalidPasswordException,
)


@pytest.mark.parametrize(
    "code,msg,data,expected_str",
    [
        (
            ErrorCode.AUTH_INVALID_CREDENTIALS,
            "Invalid credentials",
            None,
            "[10001] Invalid credentials",
        ),
        (
            ErrorCode.BIZ_INSUFFICIENT_BALANCE,
            "Insufficient balance",
            {"balance": 100, "required": 200},
            "[50001] Insufficient balance",
        ),
        (
            ErrorCode.USER_NOT_FOUND,
            "User not found",
            None,
            "[20001] User not found",
        ),
        (
            ErrorCode.PERM_INSUFFICIENT,
            "Permission denied",
            None,
            "[30001] Permission denied",
        ),
        (
            ErrorCode.ROLE_INSUFFICIENT,
            "Role denied",
            None,
            "[30002] Role denied",
        ),
    ],
)
def test_business_exception_exposes_code_message_data_and_string(
    code, msg, data, expected_str
):
    exc = BusinessException(code, msg, data=data)

    assert exc.code == code
    assert exc.msg == msg
    assert exc.data == data
    assert str(exc) == expected_str


def test_domain_exception_includes_remaining_attempts_in_message_and_data():
    exc = InvalidPasswordException(remaining_attempts=3)

    assert exc.code == ErrorCode.AUTH_INVALID_PASSWORD
    assert exc.msg == "Invalid password, 3 attempts remaining"
    assert exc.data == {"remaining_attempts": 3}
    assert str(exc) == "[10002] Invalid password, 3 attempts remaining"


def test_insufficient_permission_exception_includes_required_and_user_perms():
    exc = InsufficientPermissionException(required=["admin:delete", "admin:create"])

    assert exc.code == ErrorCode.PERM_INSUFFICIENT
    assert exc.msg == "Insufficient permissions"
    assert set(exc.data["required"]) == {"admin:delete", "admin:create"}


def test_insufficient_role_exception_includes_required_and_user_roles():
    exc = InsufficientRoleException(required=["admin", "superuser"])

    assert exc.code == ErrorCode.ROLE_INSUFFICIENT
    assert exc.msg == "Insufficient roles"
    assert set(exc.data["required"]) == {"admin", "superuser"}
