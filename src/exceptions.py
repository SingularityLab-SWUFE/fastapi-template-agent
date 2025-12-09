class BusinessException(Exception):
    """
    Business domain exception with separate HTTP status code and business error code.

    Args:
        http_code: HTTP status code for the response (e.g., 400, 401, 403, 404).
        business_code: Application-specific business error code for client logic.
        msg: Human readable description of the business rule violation.
    """

    def __init__(
        self,
        http_code: int = 400,
        business_code: int | None = None,
        msg: str = "Business error"
    ):
        self.http_code = http_code
        self.business_code = business_code if business_code is not None else http_code
        self.msg = msg
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[{self.business_code}] {self.msg}"
