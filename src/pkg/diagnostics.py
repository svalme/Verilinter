from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .rules.register_rules import module_rule_runner, rule_runner, symbol_rule_runner

Diagnostic = dict[str, Any]
Severity = str
VALID_SEVERITIES = frozenset({"error", "warning", "info"})


@dataclass(frozen=True)
class RuleMetadata:
    code: str
    category: str
    default_severity: Severity
    message: str


def metadata_by_code() -> dict[str, RuleMetadata]:
    metadata: dict[str, RuleMetadata] = {}

    for runner in (rule_runner, symbol_rule_runner, module_rule_runner):
        for rule in runner._rules:
            metadata[rule.code] = RuleMetadata(
                code=rule.code,
                category=rule.category,
                default_severity=getattr(rule, "severity", "warning"),
                message=rule.message,
            )

    return metadata


def enrich_diagnostics(
    diagnostics: list[Diagnostic],
    severity_overrides: dict[str, Severity] | None = None,
) -> list[Diagnostic]:
    severity_overrides = severity_overrides or {}
    metadata = metadata_by_code()
    enriched: list[Diagnostic] = []

    for diagnostic in diagnostics:
        copy = dict(diagnostic)
        rule_metadata = metadata.get(copy["code"])
        if rule_metadata is not None:
            copy.setdefault("category", rule_metadata.category)
            copy.setdefault(
                "severity",
                severity_overrides.get(rule_metadata.code, rule_metadata.default_severity),
            )
        else:
            copy.setdefault("category", "uncategorized")
            copy.setdefault("severity", severity_overrides.get(copy["code"], "warning"))
        enriched.append(copy)

    return enriched


def sort_diagnostics(diagnostics: list[Diagnostic]) -> list[Diagnostic]:
    return sorted(
        diagnostics,
        key=lambda diagnostic: (
            str(diagnostic.get("file", "")),
            int(diagnostic.get("line", 0)),
            int(diagnostic.get("col", 0)),
            str(diagnostic.get("code", "")),
            str(diagnostic.get("message", "")),
        ),
    )


def diagnostic_signature(diagnostic: Diagnostic) -> dict[str, Any]:
    return {
        "code": diagnostic.get("code"),
        "file": diagnostic.get("file"),
        "line": diagnostic.get("line"),
        "col": diagnostic.get("col"),
        "message": diagnostic.get("message"),
    }


def write_baseline(path: Path, diagnostics: list[Diagnostic]) -> None:
    payload = {
        "version": 1,
        "diagnostics": [diagnostic_signature(diagnostic) for diagnostic in sort_diagnostics(diagnostics)],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_baseline(path: Path) -> set[tuple[Any, ...]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw.get("diagnostics", [])
    return {
        (
            item.get("code"),
            item.get("file"),
            item.get("line"),
            item.get("col"),
            item.get("message"),
        )
        for item in items
    }


def filter_by_baseline(diagnostics: list[Diagnostic], baseline_path: Path | None) -> list[Diagnostic]:
    if baseline_path is None or not baseline_path.exists():
        return diagnostics

    baseline = load_baseline(baseline_path)
    return [
        diagnostic
        for diagnostic in diagnostics
        if (
            diagnostic.get("code"),
            diagnostic.get("file"),
            diagnostic.get("line"),
            diagnostic.get("col"),
            diagnostic.get("message"),
        )
        not in baseline
    ]
