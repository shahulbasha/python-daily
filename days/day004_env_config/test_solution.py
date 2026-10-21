from dataclasses import FrozenInstanceError
from datetime import timedelta

import pytest

from .solution import ConfigError, ConsumerSettings, load_settings, parse_bool

MINIMAL = {"APP_BOOTSTRAP_SERVERS": "broker1:9092", "APP_GROUP_ID": "orders-svc"}


def problems_for(env: dict[str, str], prefix: str = "APP_") -> list[str]:
    with pytest.raises(ConfigError) as exc_info:
        load_settings(env, prefix)
    return exc_info.value.problems


# --- parse_bool ---------------------------------------------------------------------------


@pytest.mark.parametrize("raw", ["true", "TRUE", " True ", "1", "yes", "Yes", "on", "ON"])
def test_parse_bool_true(raw: str) -> None:
    assert parse_bool(raw) is True


@pytest.mark.parametrize("raw", ["false", "FALSE", "\tFalse\n", "0", "no", "NO", "off", "Off"])
def test_parse_bool_false(raw: str) -> None:
    assert parse_bool(raw) is False


@pytest.mark.parametrize("raw", ["", "  ", "maybe", "2", "y", "truthy"])
def test_parse_bool_rejects_garbage(raw: str) -> None:
    with pytest.raises(ValueError):
        parse_bool(raw)


def test_parse_bool_error_mentions_value() -> None:
    with pytest.raises(ValueError) as exc_info:
        parse_bool("enabled")
    assert "enabled" in str(exc_info.value)


# --- load_settings: happy paths ------------------------------------------------------------


def test_minimal_uses_dataclass_defaults() -> None:
    settings = load_settings(MINIMAL)
    assert settings == ConsumerSettings(bootstrap_servers=("broker1:9092",), group_id="orders-svc")


def test_all_fields() -> None:
    env = {
        "APP_BOOTSTRAP_SERVERS": " b1:9092 , b2:9092,,b3:9092 ,",
        "APP_GROUP_ID": "  orders-svc  ",
        "APP_MAX_POLL_RECORDS": "250",
        "APP_ENABLE_AUTO_COMMIT": "yes",
        "APP_SESSION_TIMEOUT_MS": "45000",
    }
    assert load_settings(env) == ConsumerSettings(
        bootstrap_servers=("b1:9092", "b2:9092", "b3:9092"),
        group_id="orders-svc",
        max_poll_records=250,
        enable_auto_commit=True,
        session_timeout=timedelta(seconds=45),
    )


def test_session_timeout_keeps_milliseconds() -> None:
    settings = load_settings({**MINIMAL, "APP_SESSION_TIMEOUT_MS": "1500"})
    assert settings.session_timeout == timedelta(milliseconds=1500)


@pytest.mark.parametrize("n", ["1", "10000"])
def test_max_poll_records_bounds_inclusive(n: str) -> None:
    assert load_settings({**MINIMAL, "APP_MAX_POLL_RECORDS": n}).max_poll_records == int(n)


def test_custom_prefix_and_foreign_keys_ignored() -> None:
    env = {
        "ORDERS_BOOTSTRAP_SERVERS": "b1:9092",
        "ORDERS_GROUP_ID": "g",
        "APP_GROUP_ID": "ignored",  # different prefix → not ours, not an error
        "PATH": "/usr/bin",
        "HOME": "/root",
    }
    settings = load_settings(env, prefix="ORDERS_")
    assert settings.group_id == "g"


def test_settings_are_immutable() -> None:
    settings = load_settings(MINIMAL)
    assert isinstance(settings.bootstrap_servers, tuple)
    with pytest.raises(FrozenInstanceError):
        settings.group_id = "other"  # type: ignore[misc]


def test_reads_only_given_mapping(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_BOOTSTRAP_SERVERS", "from-os-environ:9092")
    monkeypatch.setenv("APP_GROUP_ID", "from-os-environ")
    monkeypatch.setenv("APP_BOGUS", "x")
    assert load_settings(MINIMAL).group_id == "orders-svc"
    problems = problems_for({})
    assert len(problems) == 2


# --- load_settings: aggregated errors ------------------------------------------------------


def test_missing_required() -> None:
    problems = problems_for({})
    assert len(problems) == 2
    assert "APP_BOOTSTRAP_SERVERS" in problems[0]
    assert "APP_GROUP_ID" in problems[1]


@pytest.mark.parametrize("servers", ["", " ", ",, ,"])
def test_bootstrap_servers_with_no_items(servers: str) -> None:
    problems = problems_for({**MINIMAL, "APP_BOOTSTRAP_SERVERS": servers})
    assert len(problems) == 1
    assert "APP_BOOTSTRAP_SERVERS" in problems[0]


def test_blank_group_id() -> None:
    problems = problems_for({**MINIMAL, "APP_GROUP_ID": "   "})
    assert len(problems) == 1
    assert "APP_GROUP_ID" in problems[0]


@pytest.mark.parametrize("value", ["lots", "0", "-5", "10001", "2.5"])
def test_bad_max_poll_records(value: str) -> None:
    problems = problems_for({**MINIMAL, "APP_MAX_POLL_RECORDS": value})
    assert len(problems) == 1
    assert "APP_MAX_POLL_RECORDS" in problems[0]
    assert value in problems[0]


def test_bad_bool() -> None:
    problems = problems_for({**MINIMAL, "APP_ENABLE_AUTO_COMMIT": "sometimes"})
    assert len(problems) == 1
    assert "APP_ENABLE_AUTO_COMMIT" in problems[0]
    assert "sometimes" in problems[0]


@pytest.mark.parametrize("value", ["soon", "0", "-1"])
def test_bad_session_timeout(value: str) -> None:
    problems = problems_for({**MINIMAL, "APP_SESSION_TIMEOUT_MS": value})
    assert len(problems) == 1
    assert "APP_SESSION_TIMEOUT_MS" in problems[0]


def test_unknown_prefixed_keys_are_problems() -> None:
    problems = problems_for({**MINIMAL, "APP_MAX_POLL_RECRODS": "50", "APP_DEBUG": "1"})
    assert len(problems) == 2
    assert "APP_DEBUG" in problems[0]
    assert "APP_MAX_POLL_RECRODS" in problems[1]


def test_all_problems_reported_once_in_table_order() -> None:
    env = {
        "APP_ZZZ": "?",
        "APP_SESSION_TIMEOUT_MS": "never",
        "APP_ENABLE_AUTO_COMMIT": "perhaps",
        "APP_MAX_POLL_RECORDS": "many",
        "APP_AAA": "?",
    }
    with pytest.raises(ConfigError) as exc_info:
        load_settings(env)
    problems = exc_info.value.problems
    expected_order = [
        "APP_BOOTSTRAP_SERVERS",
        "APP_GROUP_ID",
        "APP_MAX_POLL_RECORDS",
        "APP_ENABLE_AUTO_COMMIT",
        "APP_SESSION_TIMEOUT_MS",
        "APP_AAA",
        "APP_ZZZ",
    ]
    assert len(problems) == len(expected_order)
    for problem, var in zip(problems, expected_order, strict=True):
        assert var in problem
    message = str(exc_info.value)
    assert all(var in message for var in expected_order)
