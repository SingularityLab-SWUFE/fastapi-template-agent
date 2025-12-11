from enum import IntEnum


class ErrorCode(IntEnum):
    AUTH_INVALID_CREDENTIALS = 10001
    AUTH_INVALID_PASSWORD = 10002
    AUTH_TOKEN_INVALID = 10004
    AUTH_ACCOUNT_LOCKED = 10005

    USER_NOT_FOUND = 20001
    USER_INACTIVE = 20003

    PERM_INSUFFICIENT = 30001

    DATA_VALIDATION_FAILED = 40001

    BIZ_INSUFFICIENT_BALANCE = 50001
    BIZ_ORDER_EXPIRED = 50002

    SYS_INTERNAL_ERROR = 90003


class BusinessException(Exception):
    def __init__(self, code: ErrorCode, msg: str, data: dict | None = None):
        self.code = code
        self.msg = msg
        self.data = data
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[{self.code}] {self.msg}"


class InvalidPasswordException(BusinessException):
    def __init__(self, remaining_attempts: int):
        super().__init__(
            code=ErrorCode.AUTH_INVALID_PASSWORD,
            msg=f"Invalid password, {remaining_attempts} attempts remaining",
            data={"remaining_attempts": remaining_attempts},
        )
