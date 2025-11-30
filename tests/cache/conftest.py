import pytest
from fakeredis import FakeAsyncRedis

from src.cache import LocalCache, RedisCache


@pytest.fixture
async def local_cache():
    cache = LocalCache()
    yield cache
    await cache.close()


@pytest.fixture
async def redis_cache():
    cache = RedisCache(host="localhost", port=6379, db=1)
    cache._client = FakeAsyncRedis(decode_responses=True)
    await cache.clear()
    yield cache
    await cache.clear()
    await cache.close()
