from src.core.schemas.error import ErrorCode


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


class InsufficientPermissionException(BusinessException):
    def __init__(self, user_id: int, required: list[str], user_perms: set[str]):
        super().__init__(
            code=ErrorCode.PERM_INSUFFICIENT,
            msg=f"User {user_id} lacks required permissions",
            data={
                "required": list(required),
                "user_permissions": list(user_perms),
                "user_id": user_id,
            },
        )


class InsufficientRoleException(BusinessException):
    def __init__(self, user_id: int, required: list[str], user_roles: set[str]):
        super().__init__(
            code=ErrorCode.PERM_INSUFFICIENT,
            msg=f"User {user_id} lacks required roles",
            data={
                "required": list(required),
                "user_roles": list(user_roles),
                "user_id": user_id,
            },
        )
