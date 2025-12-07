import asyncio

from src.auth.backend import RefreshTokenManager


async def test_create_refresh_token(local_cache, settings):
    manager = RefreshTokenManager(local_cache, settings)
    token = await manager.create_refresh_token(1, "Mozilla/5.0")

    assert token is not None
    assert len(token) > 0


async def test_verify_refresh_token(local_cache, settings):
    manager = RefreshTokenManager(local_cache, settings)
    token = await manager.create_refresh_token(1, "Mozilla/5.0")

    user_id = await manager.verify_refresh_token(token)
    assert user_id == 1


async def test_verify_invalid_token(local_cache, settings):
    manager = RefreshTokenManager(local_cache, settings)

    user_id = await manager.verify_refresh_token("invalid_token")
    assert user_id is None


async def test_revoke_token(local_cache, settings):
    manager = RefreshTokenManager(local_cache, settings)
    token = await manager.create_refresh_token(1, "Mozilla/5.0")

    await manager.revoke_token(token)

    user_id = await manager.verify_refresh_token(token)
    assert user_id is None


async def test_revoke_all_user_tokens(local_cache, settings):
    manager = RefreshTokenManager(local_cache, settings)
    token1 = await manager.create_refresh_token(1, "Mozilla/5.0")
    token2 = await manager.create_refresh_token(1, "Chrome/98.0")

    await manager.revoke_all_user_tokens(1)

    assert await manager.verify_refresh_token(token1) is None
    assert await manager.verify_refresh_token(token2) is None


async def test_revoke_all_user_tokens_preserves_new_tokens(local_cache, settings):
    manager = RefreshTokenManager(local_cache, settings)
    old_token = await manager.create_refresh_token(1, "Mozilla/5.0")

    await asyncio.sleep(0.01)
    await manager.revoke_all_user_tokens(1)
    await asyncio.sleep(0.01)

    new_token = await manager.create_refresh_token(1, "Chrome/98.0")

    assert await manager.verify_refresh_token(old_token) is None
    assert await manager.verify_refresh_token(new_token) == 1


async def test_token_with_no_device_info(local_cache, settings):
    manager = RefreshTokenManager(local_cache, settings)
    token = await manager.create_refresh_token(1)

    user_id = await manager.verify_refresh_token(token)
    assert user_id == 1
