import itertools
import json
from collections.abc import Iterator

import pytest

from .solution import Event, batched_events, dedupe, latest_by_key, parse_events


def line(offset: int, key: str | None = "k", partition: int = 0, value: object = None) -> str:
    return json.dumps(
        {"topic": "orders", "partition": partition, "offset": offset, "key": key, "value": value}
    )


def ev(offset: int, key: str | None = "k", partition: int = 0, value: object = None) -> Event:
    return Event("orders", partition, offset, key, value)


def endless_lines() -> Iterator[str]:
    for n in itertools.count():
        yield line(n, key=f"k{n % 3}", value=n)


# --- parse_events -------------------------------------------------------------------------


def test_parse_events_basic() -> None:
    events = list(parse_events([line(0, value={"qty": 1}), line(1, key=None)]))
    assert events == [ev(0, value={"qty": 1}), ev(1, key=None)]


def test_parse_events_skips_blank_lines() -> None:
    assert list(parse_events(["", line(0), "   \n", line(1), "\t"])) == [ev(0), ev(1)]


def test_parse_events_bad_json_reports_line_number_after_yielding_earlier() -> None:
    it = parse_events([line(0), "", "{not json", line(3)])
    assert next(it) == ev(0)
    with pytest.raises(ValueError, match=r"line 3\b"):
        next(it)


def test_parse_events_is_lazy() -> None:
    first_two = list(itertools.islice(parse_events(endless_lines()), 2))
    assert [e.offset for e in first_two] == [0, 1]


# --- dedupe -------------------------------------------------------------------------------


def test_dedupe_drops_redeliveries_keeps_order() -> None:
    events = [ev(0), ev(1), ev(0), ev(2), ev(1)]
    assert list(dedupe(events)) == [ev(0), ev(1), ev(2)]


def test_dedupe_identity_includes_partition_and_topic() -> None:
    other_topic = Event("payments", 0, 0, "k", None)
    events = [ev(0, partition=0), ev(0, partition=1), other_topic, ev(0, partition=1)]
    assert list(dedupe(events)) == [ev(0, partition=0), ev(0, partition=1), other_topic]


def test_dedupe_is_lazy_and_accepts_one_shot_iterator() -> None:
    redelivering = (ev(n // 2) for n in itertools.count())  # 0,0,1,1,2,2,...
    assert [e.offset for e in itertools.islice(dedupe(redelivering), 3)] == [0, 1, 2]


# --- batched_events -----------------------------------------------------------------------


def test_batched_events_full_and_partial() -> None:
    events = [ev(n) for n in range(5)]
    batches = list(batched_events(iter(events), 2))
    assert batches == [[ev(0), ev(1)], [ev(2), ev(3)], [ev(4)]]
    assert all(isinstance(b, list) for b in batches)


def test_batched_events_empty_input_yields_nothing() -> None:
    assert list(batched_events([], 3)) == []


@pytest.mark.parametrize("size", [0, -1])
def test_batched_events_rejects_bad_size_at_call_time(size: int) -> None:
    with pytest.raises(ValueError):
        batched_events([], size)  # no iteration!


def test_batched_events_is_lazy() -> None:
    batches = batched_events(parse_events(endless_lines()), 4)
    assert [e.offset for e in next(batches)] == [0, 1, 2, 3]
    assert [e.offset for e in next(batches)] == [4, 5, 6, 7]


# --- latest_by_key ------------------------------------------------------------------------


def test_latest_by_key_keeps_last_and_ignores_none() -> None:
    events = [ev(0, "a", value=1), ev(1, "b", value=2), ev(2, None), ev(3, "a", value=3)]
    result = latest_by_key(events)
    assert result == {"a": ev(3, "a", value=3), "b": ev(1, "b", value=2)}


def test_latest_by_key_empty() -> None:
    assert latest_by_key(iter([])) == {}


# --- composition --------------------------------------------------------------------------


def test_full_pipeline_on_one_shot_input() -> None:
    raw = iter([line(0, "a"), line(1, "b"), line(0, "a"), "", line(2, "a")])
    batches = list(batched_events(dedupe(parse_events(raw)), 2))
    assert [[e.offset for e in b] for b in batches] == [[0, 1], [2]]
    assert next(raw, None) is None  # input consumed exactly once
