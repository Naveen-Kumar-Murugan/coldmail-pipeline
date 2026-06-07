"""
utils/rate_limiter.py
Retry / back-off helpers. Uses tenacity when available, stdlib otherwise.
"""
import time
import functools
import logging
from typing import Callable, Any

import requests

log = logging.getLogger("pipeline")

try:
    from tenacity import (
        retry, stop_after_attempt, wait_exponential,
        retry_if_exception_type, before_sleep_log,
    )
    _TENACITY = True
except ImportError:
    _TENACITY = False


class RateLimitError(Exception):
    pass


_RETRYABLE = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    requests.exceptions.ChunkedEncodingError,
)


def raise_for_rate_limit(response: requests.Response) -> None:
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 5))
        log.warning("Rate limited — sleeping %ss", retry_after)
        time.sleep(retry_after)
        raise RateLimitError(f"HTTP 429 from {response.url}")


def sleep_between(seconds: float) -> None:
    time.sleep(seconds)


def _simple_retry(fn):
    """Stdlib fallback: up to 4 attempts with exponential back-off."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        delay = 2.0
        for attempt in range(4):
            try:
                return fn(*args, **kwargs)
            except _RETRYABLE + (RateLimitError,) as exc:
                if attempt == 3:
                    raise
                log.warning("%s failed (%s) — retrying in %.1fs", fn.__name__, exc, delay)
                time.sleep(delay)
                delay = min(delay * 2, 30)
    return wrapper


if _TENACITY:
    retry_request = retry(
        retry=retry_if_exception_type(_RETRYABLE + (RateLimitError,)),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(4),
        before_sleep=before_sleep_log(log, logging.WARNING),
        reraise=True,
    )
else:
    retry_request = _simple_retry


def with_retry(max_attempts: int = 3, base_wait: float = 2.0) -> Callable:
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            delay = base_wait
            while attempt < max_attempts:
                try:
                    return fn(*args, **kwargs)
                except _RETRYABLE + (RateLimitError,) as exc:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    log.warning("%s — attempt %d/%d, retrying in %.1fs", exc, attempt, max_attempts, delay)
                    time.sleep(delay)
                    delay = min(delay * 2, 30)
        return wrapper
    return decorator