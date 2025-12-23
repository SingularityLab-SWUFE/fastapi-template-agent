import httpx
from tenacity import (
    AsyncRetrying,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)


def _should_retry(exception: BaseException) -> bool:
    if isinstance(exception, (httpx.NetworkError, httpx.TimeoutException)):
        return True
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code >= 500
    return False


def retry_on_network():
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception(_should_retry),
    )


def async_retry_on_network():
    return AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception(_should_retry),
    )
