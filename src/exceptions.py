from src.shared.errors import ErrorCode


class BusinessException(Exception):
    def __init__(self, code: ErrorCode, msg: str, data: dict | None = None):
        self.code = code
        self.msg = msg
        self.data = data
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[{self.code}] {self.msg}"
