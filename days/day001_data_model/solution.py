"""Day 001 — Make a class feel built-in. See README.md for the requirements."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from decimal import Decimal


class Position:
    """Immutable holding of one ticker. Replace this stub (hint: you may not need __init__)."""

    ticker: str
    qty: int
    avg_cost: Decimal

    def __init__(self, ticker: str, qty: int, avg_cost: Decimal) -> None:
        raise NotImplementedError

    @property
    def cost_basis(self) -> Decimal:
        raise NotImplementedError


class Portfolio:
    def __init__(self, positions: Iterable[Position] = ()) -> None:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def __iter__(self) -> Iterator[Position]:
        raise NotImplementedError

    def __contains__(self, ticker: object) -> bool:
        raise NotImplementedError

    def __getitem__(self, ticker: str) -> Position:
        raise NotImplementedError

    @property
    def total_cost(self) -> Decimal:
        raise NotImplementedError

    def __add__(self, other: object) -> Portfolio:
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError

    __hash__ = None  # type: ignore[assignment]  # mutable-looking container: not hashable
