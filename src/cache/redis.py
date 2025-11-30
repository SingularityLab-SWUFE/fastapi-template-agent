from typing import AsyncIterator

from redis.asyncio import ConnectionPool, Redis
from redis.asyncio.client import PubSub


class RedisCache:
    def __init__(
        self,
        host: str,
        port: int,
        db: int,
        password: str | None = None,
        encoding: str = "utf-8",
        decode_responses: bool = True,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        max_connections: int = 50,
        retry_on_timeout: bool = True,
    ) -> None:
        self._pool = ConnectionPool(
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
        self._client: Redis | None = None
        self._pubsub: PubSub | None = None

    @property
    def client(self) -> Redis:
        if self._client is None:
            self._client = Redis(connection_pool=self._pool)
        return self._client

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        await self.client.set(key, value, ex=ttl)

    async def get(self, key: str) -> str | None:
        return await self.client.get(key)

    async def delete(self, key: str) -> bool:
        result = await self.client.delete(key)
        return result > 0

    async def exists(self, key: str) -> bool:
        result = await self.client.exists(key)
        return result > 0

    async def keys(self, pattern: str = "*") -> list[str]:
        keys = []
        async for key in self.client.scan_iter(match=pattern):
            keys.append(key)
        return keys

    async def clear(self, pattern: str = "*") -> int:
        count = 0
        async for key in self.client.scan_iter(match=pattern):
            count += await self.client.delete(key)
        return count

    async def ttl(self, key: str) -> int:
        return await self.client.ttl(key)

    async def expire(self, key: str, ttl: int) -> bool:
        return await self.client.expire(key, ttl)

    async def publish(self, channel: str, message: str) -> int:
        return await self.client.publish(channel, message)

    async def subscribe(self, *channels: str) -> AsyncIterator[tuple[str, str]]:
        if self._pubsub is None:
            self._pubsub = self.client.pubsub()

        await self._pubsub.subscribe(*channels)

        async for message in self._pubsub.listen():
            if message["type"] == "message":
                yield (message["channel"], message["data"])

    async def close(self) -> None:
        if self._pubsub is not None:
            await self._pubsub.unsubscribe()
            await self._pubsub.aclose()
            self._pubsub = None

        if self._client is not None:
            await self._client.aclose()
            self._client = None

        await self._pool.aclose()
