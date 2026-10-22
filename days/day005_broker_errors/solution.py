"""Day 005 — Translating transport failures into domain errors. See README.md."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

# --- Provided — no changes needed ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Response:
    """What the (fake) broker HTTP transport returns."""

    status: int
    body: Mapping[str, object] = field(default_factory=dict)
    headers: Mapping[str, str] = field(default_factory=dict)


Order = Mapping[str, object]
Transport = Callable[[Order], Response]
"""Sends an order. May raise ``ConnectionError`` or ``TimeoutError`` on network failure."""


class BrokerError(Exception):
    """Base for everything the broker client raises on purpose."""


class ProtocolError(BrokerError):
    """The broker answered with something we don't understand."""


class AuthError(BrokerError):
    """Credentials rejected (401/403). Never worth retrying."""


class OrderRejected(BrokerError):
    """The broker understood the order and said no (400/422)."""

    def __init__(self, reason: str, code: str | None = None) -> None:
        super().__init__(f"order rejected: {reason}" + (f" [{code}]" if code else ""))
        self.reason = reason
        self.code = code


class RetryableError(BrokerError):
    """Transient failure — the same request may succeed later."""


class BrokerUnavailable(RetryableError):
    """5xx, or the network failed before we got a response."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class RateLimited(RetryableError):
    """429. ``retry_after`` is in seconds, or ``None`` if the broker didn't say."""

    def __init__(self, retry_after: float | None = None) -> None:
        super().__init__(f"rate limited (retry after {retry_after}s)")
        self.retry_after = retry_after


# --- Your code ----------------------------------------------------------------------------


def place_order(transport: Transport, order: Order) -> str:
    raise NotImplementedError


def place_with_retry(
    transport: Transport,
    order: Order,
    *,
    attempts: int = 3,
    base_delay: float = 0.1,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    raise NotImplementedError
