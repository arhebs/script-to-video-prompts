from __future__ import annotations


class RetryableError(Exception):
    pass


def is_retryable_exception(exc: BaseException) -> bool:
    _ = exc
    return False
