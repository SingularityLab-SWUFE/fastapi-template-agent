from time import time


class LocalCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[str, float | None]] = {}

    def _is_expired(self, expire_at: float | None) -> bool:
        if expire_at is None:
            return False
        return time() > expire_at

    def _cleanup_expired(self, key: str) -> None:
        if key in self._store:
            _, expire_at = self._store[key]
            if self._is_expired(expire_at):
                del self._store[key]

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        expire_at = time() + ttl if ttl else None
        self._store[key] = (value, expire_at)

    async def get(self, key: str) -> str | None:
        self._cleanup_expired(key)
        if key not in self._store:
            return None
        value, _ = self._store[key]
        return value

    async def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        self._cleanup_expired(key)
        return key in self._store

    async def close(self) -> None:
        self._store.clear()
