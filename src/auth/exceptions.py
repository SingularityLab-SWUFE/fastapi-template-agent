from collections.abc import Sequence

from src.exceptions import BusinessException
from src.shared.errors import ErrorCode


class InsufficientPermissionException(BusinessException):
    def __init__(self, required: Sequence[str]):
        super().__init__(
            code=ErrorCode.PERM_INSUFFICIENT,
            msg="Insufficient permissions",
            data={"required": list(required)},
        )


class InsufficientRoleException(BusinessException):
    def __init__(self, required: Sequence[str]):
        super().__init__(
            code=ErrorCode.ROLE_INSUFFICIENT,
            msg="Insufficient roles",
            data={"required": list(required)},
        )
