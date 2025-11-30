import asyncio


async def test_set_get(redis_cache):
    await redis_cache.set("key1", "value1")
    result = await redis_cache.get("key1")
    assert result == "value1"


async def test_get_nonexistent_key(redis_cache):
    result = await redis_cache.get("nonexistent")
    assert result is None


async def test_set_with_ttl(redis_cache):
    await redis_cache.set("key_ttl", "value", ttl=60)
    ttl = await redis_cache.ttl("key_ttl")
    assert 55 <= ttl <= 60


async def test_delete(redis_cache):
    await redis_cache.set("key2", "value2")
    assert await redis_cache.delete("key2")
    assert await redis_cache.get("key2") is None


async def test_delete_nonexistent_key(redis_cache):
    assert not await redis_cache.delete("nonexistent")


async def test_exists(redis_cache):
    await redis_cache.set("key3", "value3")
    assert await redis_cache.exists("key3")
    assert not await redis_cache.exists("nonexistent")


async def test_keys_pattern(redis_cache):
    await redis_cache.set("user:1", "alice")
    await redis_cache.set("user:2", "bob")
    await redis_cache.set("post:1", "content")

    user_keys = await redis_cache.keys("user:*")
    assert len(user_keys) == 2
    assert all(k.startswith("user:") for k in user_keys)


async def test_clear_pattern(redis_cache):
    await redis_cache.set("test:1", "value1")
    await redis_cache.set("test:2", "value2")
    await redis_cache.set("other:1", "value3")

    count = await redis_cache.clear("test:*")
    assert count == 2
    assert await redis_cache.get("other:1") == "value3"
    assert await redis_cache.get("test:1") is None


async def test_expire(redis_cache):
    await redis_cache.set("key_expire", "value")
    assert await redis_cache.expire("key_expire", 60)
    ttl = await redis_cache.ttl("key_expire")
    assert 55 <= ttl <= 60


async def test_ttl_nonexistent_key(redis_cache):
    ttl = await redis_cache.ttl("nonexistent")
    assert ttl == -2


async def test_pubsub(redis_cache):
    messages = []

    async def subscriber():
        async for channel, message in redis_cache.subscribe("test_channel"):
            messages.append((channel, message))
            if len(messages) >= 2:
                break

    task = asyncio.create_task(subscriber())
    await asyncio.sleep(0.1)

    await redis_cache.publish("test_channel", "msg1")
    await redis_cache.publish("test_channel", "msg2")

    await task
    assert len(messages) == 2
    assert messages[0] == ("test_channel", "msg1")
    assert messages[1] == ("test_channel", "msg2")
