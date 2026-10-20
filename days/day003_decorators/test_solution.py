import inspect
import logging
import re

import pytest

from . import solution
from .solution import timed, ttl_cache

LOGGER = solution.__name__


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class Feed:
    """Counts calls so tests can see cache hits vs misses."""

    def __init__(self) -> None:
        self.calls = 0

    def price(self, symbol: str, venue: str = "XNAS") -> float:
        self.calls += 1
        return float(len(symbol) + self.calls)


# --- timed --------------------------------------------------------------------------------


def test_timed_returns_result_and_logs_debug(caplog: pytest.LogCaptureFixture) -> None:
    @timed
    def get_price(symbol: str) -> float:
        return 101.5

    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        assert get_price("AAPL") == 101.5

    [record] = [r for r in caplog.records if r.name == LOGGER]
    assert record.levelno == logging.DEBUG
    assert re.fullmatch(r".*get_price took \d+(\.\d+)? ms", record.getMessage())


def test_timed_logs_warning_and_reraises_original(caplog: pytest.LogCaptureFixture) -> None:
    boom = ConnectionError("feed down")

    @timed
    def get_price(symbol: str) -> float:
        raise boom

    with caplog.at_level(logging.DEBUG, logger=LOGGER), pytest.raises(ConnectionError) as exc:
        get_price("AAPL")

    assert exc.value is boom
    [record] = [r for r in caplog.records if r.name == LOGGER]
    assert record.levelno == logging.WARNING
    assert re.fullmatch(r".*get_price failed after \d+(\.\d+)? ms", record.getMessage())


def test_timed_uses_qualname(caplog: pytest.LogCaptureFixture) -> None:
    class Client:
        @timed
        def fetch(self) -> int:
            return 1

    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        Client().fetch()
    assert "Client.fetch took" in caplog.text


def test_timed_preserves_metadata() -> None:
    def get_price(symbol: str) -> float:
        """Docs for get_price."""
        return 1.0

    wrapped = timed(get_price)
    assert wrapped.__name__ == "get_price"
    assert wrapped.__qualname__ == get_price.__qualname__
    assert wrapped.__doc__ == "Docs for get_price."
    assert wrapped.__wrapped__ is get_price  # type: ignore[attr-defined]


# --- ttl_cache ----------------------------------------------------------------------------


def test_ttl_cache_hits_within_ttl_and_refreshes_after() -> None:
    clock, feed = FakeClock(), Feed()
    price = ttl_cache(5.0, clock=clock)(feed.price)

    first = price("AAPL")
    clock.now += 4.999
    assert price("AAPL") == first
    assert feed.calls == 1

    clock.now += 0.001  # exactly ttl since stored -> stale
    refreshed = price("AAPL")
    assert feed.calls == 2
    assert refreshed != first

    clock.now += 1.0
    assert price("AAPL") == refreshed  # refreshed entry is fresh again
    assert feed.calls == 2


def test_ttl_cache_keys_on_args_and_kwargs() -> None:
    clock, feed = FakeClock(), Feed()
    price = ttl_cache(5.0, clock=clock)(feed.price)

    price("AAPL")
    price("MSFT")
    price("AAPL", venue="XLON")
    assert feed.calls == 3

    price("AAPL")
    price("AAPL", venue="XLON")
    assert feed.calls == 3


def test_ttl_cache_kwarg_order_does_not_matter() -> None:
    calls: list[tuple[int, int]] = []

    @ttl_cache(5.0, clock=FakeClock())
    def spread(*, bid: int, ask: int) -> int:
        calls.append((bid, ask))
        return ask - bid

    assert spread(bid=1, ask=3) == 2
    assert spread(ask=3, bid=1) == 2
    assert calls == [(1, 3)]


def test_ttl_cache_does_not_cache_exceptions() -> None:
    attempts = 0

    @ttl_cache(5.0, clock=FakeClock())
    def flaky(symbol: str) -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise TimeoutError
        return symbol

    with pytest.raises(TimeoutError):
        flaky("AAPL")
    assert flaky("AAPL") == "AAPL"
    assert flaky("AAPL") == "AAPL"
    assert attempts == 2


def test_ttl_cache_each_function_has_its_own_cache() -> None:
    clock = FakeClock()
    cache = ttl_cache(5.0, clock=clock)

    @cache
    def bid(symbol: str) -> str:
        return f"bid:{symbol}"

    @cache
    def ask(symbol: str) -> str:
        return f"ask:{symbol}"

    assert bid("AAPL") == "bid:AAPL"
    assert ask("AAPL") == "ask:AAPL"


@pytest.mark.parametrize("ttl", [0, -1.5])
def test_ttl_cache_rejects_bad_ttl_at_creation(ttl: float) -> None:
    with pytest.raises(ValueError):
        ttl_cache(ttl)  # nothing decorated, nothing called


def test_ttl_cache_uses_monotonic_by_default() -> None:
    @ttl_cache(60.0)
    def now_ish() -> object:
        return object()

    assert now_ish() is now_ish()


def test_ttl_cache_preserves_metadata() -> None:
    def get_price(symbol: str) -> float:
        """Docs for get_price."""
        return 1.0

    wrapped = ttl_cache(1.0)(get_price)
    assert wrapped.__name__ == "get_price"
    assert wrapped.__doc__ == "Docs for get_price."
    assert wrapped.__wrapped__ is get_price  # type: ignore[attr-defined]


# --- stacking -----------------------------------------------------------------------------


def test_stacked_logs_on_cache_hits_and_unwraps(caplog: pytest.LogCaptureFixture) -> None:
    feed = Feed()

    def get_price(symbol: str) -> float:
        return feed.price(symbol)

    stacked = timed(ttl_cache(5.0, clock=FakeClock())(get_price))

    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        stacked("AAPL")
        stacked("AAPL")

    assert feed.calls == 1
    assert len([r for r in caplog.records if r.name == LOGGER]) == 2
    assert inspect.unwrap(stacked) is get_price


def test_provided_quote_total_works() -> None:
    assert solution.quote_total("AAPL", 3) == 12
