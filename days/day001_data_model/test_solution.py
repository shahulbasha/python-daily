from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from .solution import Portfolio, Position


def pos(ticker: str, qty: int, cost: str) -> Position:
    return Position(ticker, qty, Decimal(cost))


# --- Position -----------------------------------------------------------------------------


def test_position_fields_and_cost_basis() -> None:
    p = pos("AAPL", 10, "150.50")
    assert (p.ticker, p.qty, p.avg_cost) == ("AAPL", 10, Decimal("150.50"))
    assert p.cost_basis == Decimal("1505.00")


def test_position_is_immutable() -> None:
    p = pos("AAPL", 10, "150")
    with pytest.raises((FrozenInstanceError, AttributeError)):
        p.qty = 20  # type: ignore[misc]
    with pytest.raises(AttributeError):
        p.cost_basis = Decimal("1")  # type: ignore[misc]


def test_position_value_equality_and_hash() -> None:
    assert pos("MSFT", 5, "300") == pos("MSFT", 5, "300")
    assert len({pos("MSFT", 5, "300"), pos("MSFT", 5, "300")}) == 1


@pytest.mark.parametrize(
    ("ticker", "qty"),
    [("", 10), ("aapl", 10), ("Aapl", 10), ("AAPL", 0), ("AAPL", -5)],
)
def test_position_validation(ticker: str, qty: int) -> None:
    with pytest.raises(ValueError):
        pos(ticker, qty, "100")


# --- Portfolio container protocol ------------------------------------------------------------


@pytest.fixture
def portfolio() -> Portfolio:
    return Portfolio([pos("NVDA", 4, "120"), pos("AAPL", 10, "150"), pos("SHOP", 20, "90")])


def test_len_iter_preserve_insertion_order(portfolio: Portfolio) -> None:
    assert len(portfolio) == 3
    assert [p.ticker for p in portfolio] == ["NVDA", "AAPL", "SHOP"]


def test_accepts_any_iterable_including_generators() -> None:
    p = Portfolio(pos(t, 1, "10") for t in ["A", "B"])
    assert len(p) == 2


def test_contains_by_ticker(portfolio: Portfolio) -> None:
    assert "AAPL" in portfolio
    assert "TSLA" not in portfolio


def test_getitem(portfolio: Portfolio) -> None:
    assert portfolio["SHOP"] == pos("SHOP", 20, "90")
    with pytest.raises(KeyError):
        portfolio["TSLA"]


def test_total_cost(portfolio: Portfolio) -> None:
    assert portfolio.total_cost == Decimal("480") + Decimal("1500") + Decimal("1800")
    assert Portfolio().total_cost == Decimal("0")


def test_duplicate_tickers_in_constructor_are_merged() -> None:
    p = Portfolio([pos("AAPL", 10, "100"), pos("AAPL", 30, "200")])
    assert len(p) == 1
    assert p["AAPL"] == pos("AAPL", 40, "175")


# --- Arithmetic ------------------------------------------------------------------------------


def test_add_merges_with_weighted_average_and_does_not_mutate() -> None:
    left = Portfolio([pos("AAPL", 10, "100"), pos("MSFT", 1, "300")])
    right = Portfolio([pos("AAPL", 30, "200"), pos("SHOP", 2, "90")])

    combined = left + right

    assert [p.ticker for p in combined] == ["AAPL", "MSFT", "SHOP"]
    assert combined["AAPL"] == pos("AAPL", 40, "175")
    assert len(left) == 2 and left["AAPL"].qty == 10
    assert len(right) == 2 and right["AAPL"].qty == 30
    assert combined is not left and combined is not right


def test_add_wrong_type_raises_type_error(portfolio: Portfolio) -> None:
    with pytest.raises(TypeError):
        portfolio + 5  # type: ignore[operator]
    with pytest.raises(TypeError):
        portfolio + [pos("AAPL", 1, "1")]  # type: ignore[operator]  # noqa: RUF005


def test_sum_of_portfolios() -> None:
    parts = [Portfolio([pos("AAPL", 1, "100")]) for _ in range(3)]
    total = sum(parts, Portfolio())
    assert total["AAPL"] == pos("AAPL", 3, "100")


def test_equality() -> None:
    a = Portfolio([pos("AAPL", 1, "100"), pos("MSFT", 1, "300")])
    b = Portfolio([pos("AAPL", 1, "100"), pos("MSFT", 1, "300")])
    assert a == b
    assert a != Portfolio([pos("AAPL", 1, "100")])
    assert a != "not a portfolio"
