# Day 004 — Typed settings from the environment

**Track:** Production craft · **Time:** 15–20 min

## Goal
Load a Kafka consumer's configuration from environment variables into an immutable, typed
settings object — and when the config is wrong, fail **once** at startup with **every**
problem listed, not one per redeploy.

## Requirements
`ConsumerSettings` (frozen dataclass) and `ConfigError` (has a `.problems: list[str]`) are
already defined in `solution.py`.

1. `parse_bool(raw)` accepts `true/false`, `1/0`, `yes/no`, `on/off` — case-insensitive,
   surrounding whitespace ignored. Anything else raises `ValueError` whose message contains
   the raw value (`repr` is fine).
2. `load_settings(env, prefix="APP_")` reads these keys from the `env` mapping:

   | Variable                        | Field                | Rules                                              |
   |---------------------------------|----------------------|----------------------------------------------------|
   | `{prefix}BOOTSTRAP_SERVERS`     | `bootstrap_servers`  | **required**; comma-separated; trim each item, drop empty items; at least one must remain |
   | `{prefix}GROUP_ID`              | `group_id`           | **required**; trimmed; must not be blank            |
   | `{prefix}MAX_POLL_RECORDS`      | `max_poll_records`   | optional int, `1 ≤ n ≤ 10_000`                      |
   | `{prefix}ENABLE_AUTO_COMMIT`    | `enable_auto_commit` | optional, via `parse_bool`                          |
   | `{prefix}SESSION_TIMEOUT_MS`    | `session_timeout`    | optional int `> 0`, milliseconds → `timedelta`      |

3. Optional variables that are absent fall back to the **dataclass defaults** — don't repeat
   `500`, `False` or `10 s` anywhere in `load_settings`.
4. Any key that starts with `prefix` but isn't in the table is a problem too
   (`APP_MAX_POLL_RECRODS=50` is a typo you want caught, not silently ignored). Keys without
   the prefix are ignored.
5. Validation is **aggregated**: collect every problem, then raise a single `ConfigError`.
   Each problem string names the offending variable (e.g. `"APP_GROUP_ID is required"`,
   `"APP_MAX_POLL_RECORDS: expected an int, got 'lots'"`). Problems appear in the order of
   the table above, then unknown keys sorted by name.
6. `load_settings` reads **only** the mapping it's given — never `os.environ` directly. (The
   caller in `main()` would pass `os.environ`; tests pass plain dicts.)

## Run
```bash
uv run pytest days/day004_env_config -q
uv run ruff check days/day004_env_config
uv run mypy days/day004_env_config
```

## Java instinct vs Python
- `Boolean.parseBoolean("yes")` is just `false`, but Python's built-in conversion to `bool`
  is worse: try `bool("false")` in a REPL before you write requirement 1.
- In Spring, `@ConfigurationProperties` + `@Validated` do the binding and collect errors for
  you. Here there's no framework — resist building a `SettingsBuilder` with setters. A
  `dict` of keyword arguments that you only fill for keys that were present gets you
  requirement 3 for free.
- `int(" 42 ")` and `int("4_2")` both succeed. Decide whether you care — but know it.

## Stretch
Make the loader generic: `load(cls: type[T], env, prefix) -> T` for **any** frozen dataclass,
driven by `dataclasses.fields()` and `typing.get_type_hints()`, with a small dict mapping
types (`int`, `bool`, `timedelta`, `tuple[str, ...]`) to parser functions. Keep mypy strict
happy with a bound `TypeVar` or PEP 695 syntax.
