from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised only on Python < 3.11
    import tomli as tomllib

from .diagnostics import VALID_SEVERITIES
from .rules.profiles import available_rule_profiles
from .rules.rule_selection import RuleSelection


@dataclass(frozen=True)
class LintConfig:
    profile: str | None = None
    rules: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    defines: tuple[str, ...] = ()
    fmt: str = "text"
    jobs: int = 1
    severity_overrides: dict[str, str] = field(default_factory=dict)
    baseline_path: Path | None = None
    store_path: Path | None = None
    use_cache: bool = True
    output_path: Path | None = None
    fail_on_error: bool = False
    fail_on_warning: bool = False
    exit_zero: bool = False
    defines_explicit: bool = False
    fmt_explicit: bool = False
    jobs_explicit: bool = False
    use_cache_explicit: bool = False
    output_path_explicit: bool = False
    fail_on_error_explicit: bool = False
    fail_on_warning_explicit: bool = False
    exit_zero_explicit: bool = False

    def to_rule_selection(self) -> RuleSelection | None:
        enabled_codes = frozenset(self.rules) if self.rules else None
        enabled_categories = frozenset(self.categories) if self.categories else None
        enabled_profiles = frozenset({self.profile}) if self.profile and self.profile != "all" else None

        if enabled_codes is None and enabled_categories is None and enabled_profiles is None:
            return None

        return RuleSelection(
            enabled_codes=enabled_codes,
            enabled_categories=enabled_categories,
            enabled_profiles=enabled_profiles,
        )


def find_default_config(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    candidates = (".verilinter.toml", "verilinter.toml")

    for directory in (current, *current.parents):
        for candidate in candidates:
            path = directory / candidate
            if path.exists():
                return path
    return None


def _parse_string_list(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"config field '{field_name}' must be a non-empty string list")
    return tuple(value)


def _parse_severity_map(value: Any) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("config field 'severity' must be a table of RULE_CODE = severity")

    parsed: dict[str, str] = {}
    for code, severity in value.items():
        if not isinstance(code, str) or not isinstance(severity, str):
            raise ValueError("severity overrides must map string rule codes to string severities")
        normalized = severity.lower()
        if normalized not in VALID_SEVERITIES:
            valid = ", ".join(sorted(VALID_SEVERITIES))
            raise ValueError(f"invalid severity '{severity}' for '{code}'; expected one of: {valid}")
        parsed[code] = normalized
    return parsed


def load_config(path: Path) -> LintConfig:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    data = payload.get("verilinter", payload)

    if not isinstance(data, dict):
        raise ValueError("config root must be a TOML table")

    profile = data.get("profile")
    if profile is not None:
        if not isinstance(profile, str):
            raise ValueError("config field 'profile' must be a string")
        if profile not in available_rule_profiles():
            available = ", ".join(available_rule_profiles())
            raise ValueError(f"unknown rule profile '{profile}'; available profiles: {available}")

    jobs = data.get("jobs", 1)
    if not isinstance(jobs, int) or jobs < 1:
        raise ValueError("config field 'jobs' must be an integer >= 1")

    fmt = data.get("format", "text")
    if fmt not in {"text", "json", "sarif"}:
        raise ValueError("config field 'format' must be one of: text, json, sarif")

    baseline_path = data.get("baseline")
    if baseline_path is not None and not isinstance(baseline_path, str):
        raise ValueError("config field 'baseline' must be a string path")
    store_path = data.get("store")
    if store_path is not None and not isinstance(store_path, str):
        raise ValueError("config field 'store' must be a string path")
    use_cache = data.get("cache", True)
    if not isinstance(use_cache, bool):
        raise ValueError("config field 'cache' must be true or false")

    output_val = data.get("output", data.get("output_path"))
    if output_val is not None and not isinstance(output_val, str):
        raise ValueError("config field 'output' must be a string path")

    fail_on_error = data.get("fail_on_error", False)
    if not isinstance(fail_on_error, bool):
        raise ValueError("config field 'fail_on_error' must be true or false")

    fail_on_warning = data.get("fail_on_warning", False)
    if not isinstance(fail_on_warning, bool):
        raise ValueError("config field 'fail_on_warning' must be true or false")

    exit_zero = data.get("exit_zero", False)
    if not isinstance(exit_zero, bool):
        raise ValueError("config field 'exit_zero' must be true or false")

    return LintConfig(
        profile=profile,
        rules=_parse_string_list(data.get("rules"), "rules"),
        categories=_parse_string_list(data.get("categories"), "categories"),
        defines=_parse_string_list(data.get("defines"), "defines"),
        fmt=fmt,
        jobs=jobs,
        severity_overrides=_parse_severity_map(data.get("severity")),
        baseline_path=(path.parent / baseline_path).resolve() if baseline_path else None,
        store_path=(path.parent / store_path).resolve() if store_path else None,
        use_cache=use_cache,
        output_path=(path.parent / output_val).resolve() if output_val else None,
        fail_on_error=fail_on_error,
        fail_on_warning=fail_on_warning,
        exit_zero=exit_zero,
        defines_explicit="defines" in data,
        fmt_explicit="format" in data,
        jobs_explicit="jobs" in data,
        use_cache_explicit=("store" in data) or ("cache" in data),
        output_path_explicit=("output" in data) or ("output_path" in data),
        fail_on_error_explicit="fail_on_error" in data,
        fail_on_warning_explicit="fail_on_warning" in data,
        exit_zero_explicit="exit_zero" in data,
    )


def merge_config(base: LintConfig, override: LintConfig) -> LintConfig:
    return LintConfig(
        profile=override.profile if override.profile is not None else base.profile,
        rules=override.rules or base.rules,
        categories=override.categories or base.categories,
        defines=override.defines if override.defines_explicit else base.defines,
        fmt=override.fmt if override.fmt_explicit else base.fmt,
        jobs=override.jobs if override.jobs_explicit else base.jobs,
        severity_overrides={**base.severity_overrides, **override.severity_overrides},
        baseline_path=override.baseline_path if override.baseline_path is not None else base.baseline_path,
        store_path=override.store_path if override.store_path is not None else base.store_path,
        use_cache=override.use_cache if override.use_cache_explicit else base.use_cache,
        output_path=override.output_path if override.output_path_explicit else base.output_path,
        fail_on_error=override.fail_on_error if override.fail_on_error_explicit else base.fail_on_error,
        fail_on_warning=override.fail_on_warning if override.fail_on_warning_explicit else base.fail_on_warning,
        exit_zero=override.exit_zero if override.exit_zero_explicit else base.exit_zero,
        defines_explicit=base.defines_explicit or override.defines_explicit,
        fmt_explicit=base.fmt_explicit or override.fmt_explicit,
        jobs_explicit=base.jobs_explicit or override.jobs_explicit,
        use_cache_explicit=base.use_cache_explicit or override.use_cache_explicit,
        output_path_explicit=base.output_path_explicit or override.output_path_explicit,
        fail_on_error_explicit=base.fail_on_error_explicit or override.fail_on_error_explicit,
        fail_on_warning_explicit=base.fail_on_warning_explicit or override.fail_on_warning_explicit,
        exit_zero_explicit=base.exit_zero_explicit or override.exit_zero_explicit,
    )


def config_from_cli(
    *,
    profile: str | None,
    rules: list[str] | None,
    categories: list[str] | None,
    defines: list[str] | None = None,
    fmt: str | None,
    jobs: int | None,
    severity: list[str] | None,
    baseline: str | None,
    store: str | None,
    no_cache: bool,
    output: str | None = None,
    fail_on_error: bool = False,
    fail_on_warning: bool = False,
    exit_zero: bool = False,
) -> LintConfig:
    overrides: dict[str, str] = {}
    for entry in severity or []:
        if "=" not in entry:
            raise ValueError(f"invalid --severity value '{entry}'; expected RULE_CODE=severity")
        code, level = entry.split("=", 1)
        normalized = level.lower()
        if normalized not in VALID_SEVERITIES:
            valid = ", ".join(sorted(VALID_SEVERITIES))
            raise ValueError(f"invalid severity '{level}' for '{code}'; expected one of: {valid}")
        overrides[code] = normalized

    return LintConfig(
        profile=profile,
        rules=tuple(rules or ()),
        categories=tuple(categories or ()),
        defines=tuple(defines or ()),
        fmt=fmt or "text",
        jobs=jobs or 1,
        severity_overrides=overrides,
        baseline_path=Path(baseline).resolve() if baseline else None,
        store_path=Path(store).resolve() if store else None,
        use_cache=not no_cache,
        output_path=Path(output).resolve() if output else None,
        fail_on_error=fail_on_error,
        fail_on_warning=fail_on_warning,
        exit_zero=exit_zero,
        defines_explicit=bool(defines),
        fmt_explicit=fmt is not None,
        jobs_explicit=jobs is not None,
        use_cache_explicit=(store is not None) or no_cache,
        output_path_explicit=output is not None,
        fail_on_error_explicit=fail_on_error,
        fail_on_warning_explicit=fail_on_warning,
        exit_zero_explicit=exit_zero,
    )
