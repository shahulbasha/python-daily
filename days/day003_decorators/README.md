# Day 003 — Typed decorators for a market-data client

**Track:** Idiomatic core · **Time:** 15–20 min

## Goal
Write two reusable, **fully typed** decorators — call timing and a TTL cache — that you could
drop onto any function in a market-data client without losing its signature, name, docstring,
or mypy's knowledge of its argument and return types.

## Requirements
1. `timed(func)` — a plain decorator (used as `@timed`, no parentheses).
   - On success, logs at **DEBUG** on the module logger (`logging.getLogger(__name__)`):
     `"<qualname> took <ms> ms"` (e.g. `"get_price took 0.4 ms"`), and returns the result.
   - If the call raises, logs at **WARNING** `"<qualname> failed after <ms> ms"` and re-raises
     the **original** exception unchanged.
   - The wrapper keeps `__name__`, `__qualname__`, `__doc__`, and exposes `__wrapped__`.
2. `ttl_cache(ttl, *, clock=time.monotonic)` — a decorator **factory** (used as
   `@ttl_cache(5.0)`).
   - Caches return values keyed by the call's positional and keyword arguments; keyword
     order must not matter (`f(a=1, b=2)` and `f(b=2, a=1)` share an entry).
   - An entry is fresh while `clock() - stored_at < ttl`; once stale, the function is called
     again and the entry refreshed.
   - Exceptions are **not** cached — the next call retries.
   - Every decorated function gets its **own** cache.
   - `ttl <= 0` raises `ValueError` when the decorator is **created** — i.e. on the
     `ttl_cache(0)` call itself, before anything is decorated or called.
   - Same metadata rules as `timed`.
3. They stack: `@timed` on top of `@ttl_cache(...)` logs a timing for cache hits too, and
   `inspect.unwrap()` on the result reaches the original undecorated function.
4. The signatures in `solution.py` are already typed with `ParamSpec`. Keep them — mypy strict
   must still see `get_price("AAPL")` as returning `Decimal` (see `quote_total` at the bottom).

## Run
```bash
uv run pytest days/day003_decorators -q
uv run ruff check days/day003_decorators
uv run mypy days/day003_decorators
```

## Java instinct vs Python
- In Spring this is an `@Aspect` with `@Around` and a proxy. Here a decorator is just a
  function returning a function — no framework, no proxy class. But a bare inner function
  loses the identity of what it wraps; the stdlib has a one-liner for that.
- `ttl_cache` has **three** layers of `def`. Think about which layer runs once at import
  time, which runs once per decorated function, and which runs per call — then put the
  validation and the cache dict in the right one.
- Building a cache key from `*args, **kwargs` is where Java folks reach for `Arrays.asList` and
  a custom `equals`. Python already has hashable immutable containers; just make sure keyword
  order can't leak into the key.

## Stretch
Give `ttl_cache`-decorated functions a `.cache_clear()` method **and keep mypy strict happy**
when callers use it — hint: a plain `Callable[P, R]` has no such attribute, so you'll need a
`Protocol` that is generic over `P` and `R`.
