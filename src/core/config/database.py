from typing import Literal

from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    driver: Literal["postgresql", "sqlite"] = "postgresql"
    host: str = "localhost"
    port: int = 5432
    user: str = ""
    password: str = ""
    database: str = ""
    echo: bool = False

    @property
    def url(self) -> str:
        if self.driver == "sqlite":
            return f"sqlite+aiosqlite:///{self.database}"
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
