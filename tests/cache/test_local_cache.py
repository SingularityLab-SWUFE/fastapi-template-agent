import asyncio


async def test_set_get(local_cache):
    await local_cache.set("key1", "value1")
    result = await local_cache.get("key1")
    assert result == "value1"


async def test_get_nonexistent_key(local_cache):
    result = await local_cache.get("nonexistent")
    assert result is None


async def test_set_with_ttl(local_cache):
    await local_cache.set("key_ttl", "value", ttl=0.1)
    assert await local_cache.exists("key_ttl")
    await asyncio.sleep(0.11)
    assert not await local_cache.exists("key_ttl")
    assert await local_cache.get("key_ttl") is None


async def test_delete(local_cache):
    await local_cache.set("key2", "value2")
    assert await local_cache.delete("key2")
    assert await local_cache.get("key2") is None


async def test_delete_nonexistent_key(local_cache):
    assert not await local_cache.delete("nonexistent")


async def test_exists(local_cache):
    await local_cache.set("key3", "value3")
    assert await local_cache.exists("key3")
    assert not await local_cache.exists("nonexistent")


async def test_close(local_cache):
    await local_cache.set("key4", "value4")
    await local_cache.close()
    assert await local_cache.get("key4") is None
