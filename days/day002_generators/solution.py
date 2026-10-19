"""Day 002 — A lazy Kafka-style consumer pipeline. See README.md for the requirements."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Event:
    """One record from a Kafka-like log. Provided — no changes needed."""

    topic: str
    partition: int
    offset: int
    key: str | None
    value: Any


def parse_events(lines: Iterable[str]) -> Iterator[Event]:
    raise NotImplementedError


def dedupe(events: Iterable[Event]) -> Iterator[Event]:
    raise NotImplementedError


def batched_events(events: Iterable[Event], size: int) -> Iterator[list[Event]]:
    raise NotImplementedError


def latest_by_key(events: Iterable[Event]) -> dict[str, Event]:
    raise NotImplementedError
