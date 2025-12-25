from pydantic import Field
from pydantic_settings import BaseSettings


class LogSettings(BaseSettings):
    level: str = Field(default="INFO")
    json_logs: bool = Field(default=False)
