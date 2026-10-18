# python-daily

Daily 15–20 minute Python drills for an experienced Java/Spring engineer, reviewed every morning
like a senior Python code review.

## The loop

1. **~6:30 am** — a scheduled reviewer runs. It reviews yesterday's solution (runs tests, ruff,
   mypy), writes `REVIEW.md` into that day's folder, updates `PROGRESS.md`, and adds today's
   exercise under `days/`.
2. **You** — `git pull`, open the newest `days/dayNNN_*` folder, read its `README.md`, fill in
   `solution.py`, then commit and push before the next morning.
3. Repeat. Recurring mistakes in `PROGRESS.md` steer which exercises come next.

## Commands

```bash
uv sync                                   # once
uv run pytest days/day001_data_model      # today's tests
uv run ruff check . && uv run ruff format --check .
uv run mypy days/day001_data_model
```

A solution is "done" when tests pass **and** ruff + mypy (strict) are clean. The review then
focuses on whether it's idiomatic, not whether it works.

## Weekly rotation

| Day | Track | Focus |
|-----|-------|-------|
| Mon, Tue | Idiomatic core | data model & dunders, iterators/generators, decorators, context managers, typing, dataclasses |
| Wed, Thu | Production craft | pytest fixtures/parametrize, packaging & layout, logging, config, errors, mypy-driven design |
| Fri | AI engineering | asyncio, Pydantic, httpx, retries/backoff, streaming, LLM client & tool patterns |
| Sat, Sun | Weekend build | slightly longer (30–40 min) mini-build combining the week's topics |

Busy days are fine — solve two at once, or a whole week on Friday. The reviewer reviews whatever
is unreviewed, adds at most one exercise per morning, and stops adding once **5 are pending**
until you catch up.
