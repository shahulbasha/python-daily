"""Day 003 — Typed decorators for a market-data client. See README.md for the requirements."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from decimal import Decimal

logger = logging.getLogger(__name__)


def timed[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    raise NotImplementedError


def ttl_cache[**P, R](
    ttl: float, *, clock: Callable[[], float] = time.monotonic
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    raise NotImplementedError


# --- Provided: keep these type-checking once your decorators are implemented ---------------


def get_price(symbol: str) -> Decimal:
    """Pretend market-data lookup."""
    return Decimal(len(symbol))


def quote_total(symbol: str, qty: int) -> Decimal:
    # Under mypy strict this only passes if the decorators preserve `-> Decimal`.
    cached = timed(ttl_cache(5.0)(get_price))
    return cached(symbol) * qty
