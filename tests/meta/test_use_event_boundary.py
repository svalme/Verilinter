"""Meta-test keeping the reading of a symbol's use events in a known set of files.

Who writes a symbol, who reads it and which driver owns each write are answered by
`semantic/driver_resolver.py`. A file that loops over `symbol.use_events` itself decides again what counts as
a write or a driver, and can disagree with the others. A file listed below does so for a reason; a file that
starts reading `use_events` has to be added here, which is the moment to ask whether the resolver should
answer the question.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

SRC_ROOT = Path(__file__).resolve().parents[2] / "src"

READERS = {
    "pkg/semantic/driver_resolver.py": "the one resolver for writes, reads and drivers",
    "pkg/semantic/symbol.py": "owns the list and appends each event",
    "pkg/semantic/scope.py": "merges the events of a redeclared symbol",
    "pkg/semantic/symbol_serialization.py": "stores and restores the events",
    "pkg/semantic/instance_effects.py": "counts the port-connection events it has to classify",
    "pkg/rules/combinational_logic/read_before_write_rule.py": "orders reads against writes per driver and block",
}


def _reads_use_events(path: Path) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Attribute) and node.attr == "use_events"]


def test_use_events_are_read_only_in_listed_files() -> None:
    offenders: dict[str, list[int]] = {}
    for path in sorted(SRC_ROOT.rglob("*.py")):
        rel = path.relative_to(SRC_ROOT).as_posix()
        if rel in READERS:
            continue
        lines = _reads_use_events(path)
        if lines:
            offenders[rel] = lines
    assert not offenders, (
        "These files read `use_events` themselves; ask DriverResolver (write_events, read_events, drivers) "
        f"or add the file to READERS with the reason: {offenders}"
    )


def test_every_listed_file_exists_and_still_reads_use_events() -> None:
    stale = [rel for rel in READERS if not (SRC_ROOT / rel).is_file() or not _reads_use_events(SRC_ROOT / rel)]
    assert not stale, f"stale entries in READERS: {stale}"
