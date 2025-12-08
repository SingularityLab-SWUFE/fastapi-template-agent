class BusinessException(Exception):
    """Business domain exception that keeps HTTP-agnostic metadata."""

    def __init__(self, code: int = 400, msg: str = "Business error"):
        self.code = code
        self.msg = msg
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[{self.code}] {self.msg}"
