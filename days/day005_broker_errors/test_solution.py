from collections.abc import Iterable

import pytest

from .solution import (
    AuthError,
    BrokerError,
    BrokerUnavailable,
    Order,
    OrderRejected,
    ProtocolError,
    RateLimited,
    Response,
    RetryableError,
    place_order,
    place_with_retry,
)

ORDER: Order = {"symbol": "AAPL", "qty": 10, "side": "buy"}


class FakeTransport:
    """Plays back a script of responses or exceptions, recording each call."""

    def __init__(self, script: Iterable[Response | BaseException]) -> None:
        self.script = list(script)
        self.calls: list[Order] = []

    def __call__(self, order: Order) -> Response:
        self.calls.append(order)
        step = self.script.pop(0)
        if isinstance(step, BaseException):
            raise step
        return step


def ok(order_id: str = "ord-1") -> Response:
    return Response(200, {"order_id": order_id})


def unavailable() -> Response:
    return Response(503)


# --- place_order: success -----------------------------------------------------------------


@pytest.mark.parametrize("status", [200, 201])
def test_success_returns_order_id(status: int) -> None:
    transport = FakeTransport([Response(status, {"order_id": "ord-42"})])
    assert place_order(transport, ORDER) == "ord-42"
    assert transport.calls == [ORDER]


@pytest.mark.parametrize("body", [{}, {"order_id": ""}, {"order_id": 42}, {"order_id": None}])
def test_success_without_usable_order_id_is_protocol_error(body: dict[str, object]) -> None:
    with pytest.raises(ProtocolError):
        place_order(FakeTransport([Response(200, body)]), ORDER)


# --- place_order: status mapping ----------------------------------------------------------


@pytest.mark.parametrize("status", [400, 422])
def test_rejection_carries_reason_and_code(status: int) -> None:
    resp = Response(status, {"reason": "insufficient funds", "code": "NSF"})
    with pytest.raises(OrderRejected) as exc_info:
        place_order(FakeTransport([resp]), ORDER)
    assert exc_info.value.reason == "insufficient funds"
    assert exc_info.value.code == "NSF"


@pytest.mark.parametrize(
    ("body", "reason", "code"),
    [
        ({}, "unknown", None),
        ({"reason": 7, "code": 99}, "unknown", None),
        ({"reason": "halted"}, "halted", None),
    ],
)
def test_rejection_defaults(body: dict[str, object], reason: str, code: str | None) -> None:
    with pytest.raises(OrderRejected) as exc_info:
        place_order(FakeTransport([Response(400, body)]), ORDER)
    assert exc_info.value.reason == reason
    assert exc_info.value.code == code


@pytest.mark.parametrize("status", [401, 403])
def test_auth_errors(status: int) -> None:
    with pytest.raises(AuthError):
        place_order(FakeTransport([Response(status)]), ORDER)


@pytest.mark.parametrize(
    ("headers", "expected"),
    [({"Retry-After": "2"}, 2.0), ({"Retry-After": "0.5"}, 0.5), ({}, None)],
)
def test_rate_limited_parses_retry_after(headers: dict[str, str], expected: float | None) -> None:
    with pytest.raises(RateLimited) as exc_info:
        place_order(FakeTransport([Response(429, headers=headers)]), ORDER)
    assert exc_info.value.retry_after == expected


def test_unparsable_retry_after_is_none_and_leaves_no_value_error() -> None:
    resp = Response(429, headers={"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"})
    with pytest.raises(RateLimited) as exc_info:
        place_order(FakeTransport([resp]), ORDER)
    err = exc_info.value
    assert err.retry_after is None
    assert err.__cause__ is None
    assert err.__context__ is None


@pytest.mark.parametrize("status", [500, 502, 503, 599])
def test_server_errors_are_unavailable_with_status(status: int) -> None:
    with pytest.raises(BrokerUnavailable) as exc_info:
        place_order(FakeTransport([Response(status)]), ORDER)
    assert exc_info.value.status == status
    assert isinstance(exc_info.value, RetryableError)


@pytest.mark.parametrize("status", [204, 302, 404, 418])
def test_unexpected_status_is_protocol_error_naming_status(status: int) -> None:
    with pytest.raises(ProtocolError) as exc_info:
        place_order(FakeTransport([Response(status)]), ORDER)
    assert str(status) in str(exc_info.value)


# --- place_order: exception translation ---------------------------------------------------


@pytest.mark.parametrize("cause", [ConnectionError("reset by peer"), TimeoutError("read timeout")])
def test_network_failure_becomes_unavailable_chained(cause: OSError) -> None:
    with pytest.raises(BrokerUnavailable) as exc_info:
        place_order(FakeTransport([cause]), ORDER)
    assert exc_info.value.status is None
    assert exc_info.value.__cause__ is cause


@pytest.mark.parametrize("bug", [KeyError("price"), TypeError("bad operand"), ValueError("x")])
def test_bugs_propagate_unchanged(bug: Exception) -> None:
    with pytest.raises(type(bug)) as exc_info:
        place_order(FakeTransport([bug]), ORDER)
    assert exc_info.value is bug
    assert not isinstance(exc_info.value, BrokerError)


# --- place_with_retry ---------------------------------------------------------------------


class SleepRecorder:
    def __init__(self) -> None:
        self.delays: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


def test_first_try_success_does_not_sleep() -> None:
    sleep = SleepRecorder()
    assert place_with_retry(FakeTransport([ok()]), ORDER, sleep=sleep) == "ord-1"
    assert sleep.delays == []


def test_retries_transient_then_succeeds_with_exponential_backoff() -> None:
    sleep = SleepRecorder()
    transport = FakeTransport([unavailable(), ConnectionError("reset"), ok("ord-9")])
    result = place_with_retry(transport, ORDER, attempts=3, base_delay=0.5, sleep=sleep)
    assert result == "ord-9"
    assert len(transport.calls) == 3
    assert sleep.delays == [0.5, 1.0]


def test_rate_limit_retry_after_overrides_backoff() -> None:
    sleep = SleepRecorder()
    transport = FakeTransport([Response(429, headers={"Retry-After": "3"}), Response(429), ok()])
    place_with_retry(transport, ORDER, attempts=3, base_delay=0.1, sleep=sleep)
    assert sleep.delays == [3.0, 0.2]


@pytest.mark.parametrize(
    ("response", "error"),
    [
        (Response(400, {"reason": "bad qty"}), OrderRejected),
        (Response(401), AuthError),
        (Response(404), ProtocolError),
    ],
)
def test_non_retryable_raised_immediately(response: Response, error: type[BrokerError]) -> None:
    sleep = SleepRecorder()
    transport = FakeTransport([response, ok()])
    with pytest.raises(error):
        place_with_retry(transport, ORDER, attempts=5, sleep=sleep)
    assert len(transport.calls) == 1
    assert sleep.delays == []


def test_bug_is_not_retried() -> None:
    transport = FakeTransport([KeyError("price"), ok()])
    with pytest.raises(KeyError):
        place_with_retry(transport, ORDER, sleep=SleepRecorder())
    assert len(transport.calls) == 1


def test_exhaustion_reraises_last_error_with_note() -> None:
    sleep = SleepRecorder()
    last = Response(502)
    transport = FakeTransport([unavailable(), Response(500), last])
    with pytest.raises(BrokerUnavailable) as exc_info:
        place_with_retry(transport, ORDER, attempts=3, base_delay=0.1, sleep=sleep)
    err = exc_info.value
    assert type(err) is BrokerUnavailable
    assert err.status == 502
    assert "gave up after 3 attempts" in getattr(err, "__notes__", [])
    assert sleep.delays == [0.1, 0.2]  # no sleep after the final attempt


def test_exhaustion_keeps_network_cause() -> None:
    cause = TimeoutError("read timeout")
    transport = FakeTransport([cause])
    with pytest.raises(BrokerUnavailable) as exc_info:
        place_with_retry(transport, ORDER, attempts=1, sleep=SleepRecorder())
    assert exc_info.value.__cause__ is cause
    assert "gave up after 1 attempts" in getattr(exc_info.value, "__notes__", [])


@pytest.mark.parametrize("attempts", [0, -1])
def test_invalid_attempts(attempts: int) -> None:
    transport = FakeTransport([ok()])
    with pytest.raises(ValueError):
        place_with_retry(transport, ORDER, attempts=attempts, sleep=SleepRecorder())
    assert transport.calls == []
