import httpx
import pytest
from unittest.mock import Mock
from tenacity import RetryError

from src.retry import retry_on_network, async_retry_on_network, _should_retry


def test_should_retry_on_network_error():
    assert _should_retry(httpx.NetworkError("Connection failed"))


def test_should_retry_on_timeout():
    assert _should_retry(httpx.TimeoutException("Request timeout"))


def test_should_retry_on_5xx():
    response = Mock(status_code=500)
    exc = httpx.HTTPStatusError("Server error", request=Mock(), response=response)
    assert _should_retry(exc)


def test_should_not_retry_on_4xx():
    response = Mock(status_code=404)
    exc = httpx.HTTPStatusError("Not found", request=Mock(), response=response)
    assert not _should_retry(exc)


def test_should_not_retry_on_other_exceptions():
    assert not _should_retry(ValueError("Invalid value"))
    assert not _should_retry(KeyError("Missing key"))


def test_retry_on_network_stops_after_max_attempts():
    call_count = 0

    @retry_on_network()
    def failing_func():
        nonlocal call_count
        call_count += 1
        raise httpx.NetworkError("Connection failed")

    with pytest.raises(RetryError):
        failing_func()

    assert call_count == 3


def test_retry_on_network_succeeds_after_retry():
    call_count = 0

    @retry_on_network()
    def eventually_succeeds():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise httpx.NetworkError("Connection failed")
        return "success"

    result = eventually_succeeds()

    assert result == "success"
    assert call_count == 3


async def test_async_retry_on_network_stops_after_max_attempts():
    call_count = 0

    async def failing_func():
        nonlocal call_count
        call_count += 1
        raise httpx.NetworkError("Connection failed")

    with pytest.raises(RetryError):
        async for attempt in async_retry_on_network():
            with attempt:
                await failing_func()

    assert call_count == 3


async def test_async_retry_on_network_succeeds_after_retry():
    call_count = 0

    async def eventually_succeeds():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise httpx.NetworkError("Connection failed")
        return "success"

    result = None
    async for attempt in async_retry_on_network():
        with attempt:
            result = await eventually_succeeds()

    assert result == "success"
    assert call_count == 2


async def test_async_retry_does_not_retry_on_4xx():
    call_count = 0

    async def failing_func():
        nonlocal call_count
        call_count += 1
        response = Mock(status_code=400)
        raise httpx.HTTPStatusError("Bad request", request=Mock(), response=response)

    with pytest.raises(httpx.HTTPStatusError):
        async for attempt in async_retry_on_network():
            with attempt:
                await failing_func()

    assert call_count == 1


@pytest.mark.integration
async def test_api_call_with_retry_eventually_succeeds():
    call_count = 0

    @retry_on_network()
    async def fetch_user_data(user_id: int):
        nonlocal call_count
        call_count += 1

        if call_count < 3:
            response = Mock(status_code=503, text="Service Unavailable")
            raise httpx.HTTPStatusError(
                "Service unavailable", request=Mock(), response=response
            )
        return {"user_id": user_id, "name": "John Doe"}

    result = await fetch_user_data(123)

    assert result == {"user_id": 123, "name": "John Doe"}
    assert call_count == 3


@pytest.mark.integration
async def test_api_call_with_retry_on_network_error():
    call_count = 0

    @retry_on_network()
    async def fetch_external_api():
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            raise httpx.NetworkError("DNS resolution failed")
        elif call_count == 2:
            raise httpx.TimeoutException("Request timeout")
        else:
            return {"status": "ok", "data": [1, 2, 3]}

    result = await fetch_external_api()

    assert result == {"status": "ok", "data": [1, 2, 3]}
    assert call_count == 3
