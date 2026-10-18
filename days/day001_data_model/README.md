# Day 001 — Make a class feel built-in

**Track:** Idiomatic core · **Time:** 15–20 min

## Goal
Build a small `Portfolio` that behaves like a native Python container, so callers can use
`len()`, `for`, `in`, `[]`, `+` and even `sum()` on it — no `getSize()` / `containsTicker()`.

## Requirements
1. `Position` is an immutable value object with `ticker: str`, `qty: int`, `avg_cost: Decimal`.
   - Raise `ValueError` if `ticker` is empty or not uppercase, or if `qty <= 0`.
   - `cost_basis` is a read-only attribute: `qty * avg_cost`.
   - Two positions with the same fields are equal and hashable.
2. `Portfolio(positions=...)` accepts any iterable of `Position`.
   Duplicate tickers in the input are merged (see 5).
3. Container behaviour:
   - `len(p)` → number of distinct tickers
   - `for pos in p` → positions in the order tickers were first added
   - `"AAPL" in p` → membership by ticker string
   - `p["AAPL"]` → the `Position`; unknown ticker raises `KeyError`
4. `p.total_cost` → sum of all cost bases (`Decimal("0")` when empty).
5. `p1 + p2` returns a **new** `Portfolio`; neither operand changes. Same ticker merges into one
   position with summed qty and quantity-weighted average cost.
   Adding anything that isn't a `Portfolio` must raise `TypeError`.
6. `sum([p1, p2, p3], Portfolio())` works.
7. Two portfolios with the same positions in the same order are `==`.

## Run
```bash
uv run pytest days/day001_data_model -q
uv run ruff check days/day001_data_model
uv run mypy days/day001_data_model
```

## Java instinct vs Python
- In Java you'd write the constructor, getters, `equals`, `hashCode` and `toString` by hand.
  Python's standard library will generate nearly all of that for you — find the one decorator
  and the two arguments to it that make the class immutable and lean.
- In Java, `add(Object o)` that gets the wrong type throws. In Python, a binary operator has a
  special return value that lets the *other* operand try — and Python raises the `TypeError`
  for you. Don't raise it yourself.
- Think about which dunder method lets `in` work, and which one `sum()` quietly relies on.

## Stretch
Give `Portfolio` a readable `__repr__`, and make `Position` sort by ticker (`sorted(p)`)
without writing `__lt__` by hand.
