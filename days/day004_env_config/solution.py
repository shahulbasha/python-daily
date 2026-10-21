"""Day 004 — Typed settings from the environment. See README.md for the requirements."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True, slots=True)
class ConsumerSettings:
    """Settings for a Kafka consumer service. Provided — no changes needed."""

    bootstrap_servers: tuple[str, ...]
    group_id: str
    max_poll_records: int = 500
    enable_auto_commit: bool = False
    session_timeout: timedelta = timedelta(seconds=10)


class ConfigError(Exception):
    """Raised once, listing every configuration problem found. Provided — no changes needed."""

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__("invalid configuration:\n" + "\n".join(f"  - {p}" for p in problems))


def parse_bool(raw: str) -> bool:
    raise NotImplementedError


def load_settings(env: Mapping[str, str], prefix: str = "APP_") -> ConsumerSettings:
    raise NotImplementedError
