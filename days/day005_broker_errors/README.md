# Day 005 — Domain errors: translate, chain, retry

**Track:** Production craft · **Time:** 15–20 min

## Goal
Wrap a broker's order-placement endpoint so callers only ever see **your** exception
hierarchy — with the original cause preserved — and retry exactly the failures that are
worth retrying.

## Requirements
The hierarchy (`BrokerError` → `ProtocolError`, `AuthError`, `OrderRejected`,
`RetryableError` → `BrokerUnavailable`, `RateLimited`) and `Response` are provided in
`solution.py`. You implement two functions.

1. `place_order(transport, order)` calls `transport(order)` once and maps the outcome:

   | Outcome                                      | Result                                                        |
   |----------------------------------------------|---------------------------------------------------------------|
   | `200`/`201` with a non-empty `str` `body["order_id"]` | return it                                            |
   | `200`/`201` without a usable `order_id`      | `ProtocolError`                                               |
   | `400`/`422`                                  | `OrderRejected(reason=body["reason"], code=body.get("code"))`; missing/non-str `reason` → `"unknown"`, non-str `code` → `None` |
   | `401`/`403`                                  | `AuthError`                                                   |
   | `429`                                        | `RateLimited(retry_after)` from the `Retry-After` header as seconds (`float`); missing or unparsable → `None` |
   | any `5xx`                                    | `BrokerUnavailable(..., status=status)`                       |
   | any other status                             | `ProtocolError` whose message includes the status             |
   | transport raises `ConnectionError` / `TimeoutError` | `BrokerUnavailable(..., status=None)` whose `__cause__` **is** the original exception |

2. Anything else the transport raises (a `KeyError`, a `TypeError` — i.e. a bug) propagates
   **unchanged**. Don't turn bugs into `BrokerError`s.
3. An unparsable `Retry-After` must not leave a `ValueError` hanging off the `RateLimited`
   — neither as `__cause__` nor as `__context__`.
4. `place_with_retry(transport, order, *, attempts=3, base_delay=0.1, sleep=time.sleep)`:
   - `attempts < 1` → `ValueError`, without calling the transport.
   - Retries only `RetryableError`s. Any other `BrokerError` is raised immediately, no sleep.
   - Before retry *n* (0-based) sleep `retry_after` if the error is a `RateLimited` with one,
     otherwise `base_delay * 2**n`. Never sleep after the final attempt.
   - When attempts run out, re-raise **the last error itself** (same object, same type —
     not a new wrapper) with a note attached, `f"gave up after {attempts} attempts"`.

## Run
```bash
uv run pytest days/day005_broker_errors -q
uv run ruff check days/day005_broker_errors
uv run mypy days/day005_broker_errors
```

## Java instinct vs Python
- `throw new BrokerException(e.getMessage())` drops the cause in Java, and Python has its
  own version of that trap. Python chains implicitly when you raise inside an `except`, but
  what lands in `__cause__` and what lands in `__context__` depends on how you raise.
  Requirements 1 and 3 test the difference.
- The checked-exception reflex is to wrap everything in `except Exception:` so nothing
  "leaks". Requirement 2 says don't.
- To add context to an exception that's already in flight you don't need a new wrapper
  class. Look at what `BaseException` offers since 3.11.
- `match response.status:` with `case 200 | 201:` and guards reads better than an `if` ladder
  here. Your call.

## Stretch
Add `place_batch(transport, orders) -> list[str]`: place every order and, if any failed,
raise an `ExceptionGroup` with one exception per failed order (each carrying a note with
its index). Write a caller that uses `except* OrderRejected` and `except* RetryableError`
to handle the two kinds separately.
