from collections.abc import AsyncGenerator
from typing import Literal

from .local import LocalCache
from .protocol import CacheProtocol
from .redis import RedisCache

__all__ = [
    "CacheProtocol",
    "RedisCache",
    "LocalCache",
    "init_cache",
    "close_cache",
    "get_cache",
    "cache",
]

cache: CacheProtocol


async def init_cache(
    backend: Literal["redis", "local"] = "redis",
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    password: str | None = None,
    encoding: str = "utf-8",
    decode_responses: bool = True,
    socket_timeout: int = 5,
    socket_connect_timeout: int = 5,
    max_connections: int = 50,
    retry_on_timeout: bool = True,
) -> None:
    global cache
    if backend == "redis":
        cache = RedisCache(
            host=host,
            port=port,
            db=db,
            password=password,
            encoding=encoding,
            decode_responses=decode_responses,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            max_connections=max_connections,
            retry_on_timeout=retry_on_timeout,
        )
    else:
        cache = LocalCache()


async def close_cache() -> None:
    await cache.close()


async def get_cache() -> AsyncGenerator[CacheProtocol, None]:
    yield cache
