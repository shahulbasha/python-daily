# Day 002 — A lazy Kafka-style consumer pipeline

**Track:** Idiomatic core · **Time:** 15–20 min

## Goal
Turn a stream of raw log lines into deduplicated, batched events using **generators**, so the
pipeline handles an endless topic in constant memory — no intermediate lists.

## Requirements
`Event` is already defined for you in `solution.py` (frozen dataclass:
`topic`, `partition`, `offset`, `key`, `value`).

1. `parse_events(lines)` lazily yields one `Event` per line. Each line is a JSON object with
   keys `topic`, `partition`, `offset`, `key` (string or `null`), `value`.
   - Blank / whitespace-only lines are skipped.
   - A line that isn't valid JSON raises `ValueError` whose message contains the **1-based line
     number** (e.g. `"line 3: ..."`). Earlier events must already have been yielded.
2. `dedupe(events)` lazily drops redeliveries: an event whose `(topic, partition, offset)` was
   already seen is skipped (at-least-once delivery → effectively-once processing).
3. `batched_events(events, size)` lazily yields `list[Event]` chunks of `size`; the final chunk
   may be shorter; no empty chunks.
   - `size < 1` raises `ValueError` **at call time** — before anyone iterates the result.
4. `latest_by_key(events)` returns a `dict[str, Event]` with the **last** event per key
   (log compaction). Events with `key=None` are ignored.
5. Every step must work on a one-shot iterator and on an **infinite** stream: the tests feed
   `itertools.count()`-driven input and only take the first few results.

## Run
```bash
uv run pytest days/day002_generators -q
uv run ruff check days/day002_generators
uv run mypy days/day002_generators
```

## Java instinct vs Python
- A Java `Stream` pipeline is the right mental model — but you won't need a builder or a
  `Collector`. One keyword turns an ordinary function into a lazy producer.
- That same keyword changes *when* your function body runs. Ask yourself exactly when the
  `size < 1` check in requirement 3 fires if the whole function is a generator.
- `enumerate`, `itertools` and `set` will do most of the bookkeeping you'd write counters and
  loops for in Java. Check what `itertools` gained in 3.12.

## Stretch
Add `pipeline(lines, size)` that composes 1–3 in a single expression, and make `parse_events`
log (via `logging`) how many lines it skipped when the consumer stops early — hint: what does
a generator receive when it's closed or garbage-collected mid-iteration?
