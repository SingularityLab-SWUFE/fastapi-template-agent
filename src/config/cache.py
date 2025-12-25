from typing import Literal

from pydantic_settings import BaseSettings


class CacheSettings(BaseSettings):
    backend: Literal["redis", "local"] = "redis"
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    encoding: str = "utf-8"
    decode_responses: bool = True
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    max_connections: int = 50
    retry_on_timeout: bool = True

    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"
