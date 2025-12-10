class BusinessException(Exception):
    """
    Business domain exception with business error code.

    Args:
        business_code: Application-specific business error code for client logic.
        msg: Human readable description of the business rule violation.
        data: Additional data to include in the error response.
    """

    def __init__(
        self,
        business_code: int,
        msg: str,
        data: object | None = None
    ):
        self.business_code = business_code
        self.msg = msg
        self.data = data
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[{self.business_code}] {self.msg}"
