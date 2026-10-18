# Reviewer instructions

You are the daily reviewer for this repo. Act like a senior Python engineer reviewing a strong
Java engineer who is moving to Python. Read `README.md` and `PROGRESS.md` first.

## 1. Find work to review
- A day folder needs review when it has no `REVIEW.md` and `solution.py` differs from its
  original stub (check `git log` for commits touching it after the folder was created, or that
  `NotImplementedError` stubs are gone).
- Review every such folder, oldest first. If nothing changed, skip review — no nagging.

## 2. Review each solution
Run, from the repo root:
```bash
uv sync
uv run pytest days/<folder> -q
uv run ruff check days/<folder> && uv run ruff format --check days/<folder>
uv run mypy days/<folder>
```
Then write `days/<folder>/REVIEW.md`:

```
# Review — dayNNN
**Verdict:** Ship it / Ship with nits / Needs another pass
**Checks:** tests ✅/❌ · ruff ✅/❌ · mypy ✅/❌

## What's already Pythonic
(1–3 specific things, so good habits get reinforced)

## Changes I'd ask for
(numbered; each with: the line/snippet, why, and the idiomatic rewrite as a code block.
 Tag Java-carryover habits explicitly as **[Java habit]**.)

## One thing to read
(a single link: Python docs, PEP, or a well-known reference — on the biggest issue)
```

Priorities, in order: correctness & tests → Java habits → idiom & stdlib use → typing →
naming/structure → style nits (ruff already catches most; don't repeat its output).
Keep it to the 3–6 most valuable points. Never rewrite the whole solution for them.

## 3. Update PROGRESS.md
- Set the day's Result (e.g. `ship with nits`).
- Update **Recurring mistakes** (add on 2nd occurrence; remove after 3 clean exercises).
- Rewrite **Next focus** (1–3 bullets).

## 4. Add today's exercise
**Pending cap: at most 5 unsolved exercises at any time.** Count day folders whose
`solution.py` still has `NotImplementedError` stubs (after this run's reviews). If that count
is 5 or more, add nothing today — the learner batches work (e.g. several days on Friday), so
just leave the existing ones to finish. Never add more than one exercise per run.
Otherwise create `days/dayNNN_<slug>/` (next number) with `__init__.py`, `README.md`,
`solution.py`, `test_solution.py`, following the weekly rotation in `README.md` and steering
toward **Recurring mistakes** / **Next focus**. Never repeat a topic already in the table.

Exercise rules:
- 15–20 min (weekends 30–40). No syntax basics; assume deep Java/Spring/Kafka experience.
- Realistic domain (trading, orders, Kafka-like events, LLM calls, config, APIs) — not toy puzzles.
- `README.md`: goal, numbered requirements, how to run, a "Java instinct vs Python" hint that
  names the trap without giving the answer, and an optional stretch goal.
- `solution.py`: fully typed stubs raising `NotImplementedError`; must pass ruff + mypy as-is.
- `test_solution.py`: pytest, imports via `from .solution import ...`, covers every requirement
  and the edge cases; no network (mock or fake any I/O). Run it to confirm it fails only with
  NotImplementedError before committing.
- Add the new row to the PROGRESS.md table with Result `pending`.

## 5. Commit and report
Commit to `main` with message `review dayNNN; add dayMMM <topic>` and push.
Then send the learner a short message: verdict + top point for each review, and today's
exercise title + one-line goal + folder path.
