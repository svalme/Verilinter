"""Meta-test keeping the reading of an instance's port connections in a known set of files.

What an instance connects to each port of its child module is built once, by `semantic/connection_records.py`
(a `ConnectionRecord` per port). A rule reads those records, or the helpers in `rules/connection_analysis.py`
that wrap them; it does not pair ports with connections itself. A file that starts reading the raw
`connections` list or the port-pairing helpers has to be added here, which is the moment to ask whether the
record should carry that fact instead.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

SRC_ROOT = Path(__file__).resolve().parents[2] / "src"

PAIRING_NAMES = {"module_ports_for", "specialized_port_symbol", "bound_port_pairs", "instance_parameter_scope"}

CONNECTION_READERS = {
    "pkg/semantic/models/instance_record.py": "defines the record and its stored form",
    "pkg/semantic/connection_records.py": "builds a ConnectionRecord per port",
    "pkg/semantic/instance_ports.py": "child ports and parameter scope, used by the builder",
    "pkg/semantic/instance_effects.py": "reads each connection to decide which signals an output drives",
    "pkg/rules/connection_analysis.py": "the rule-facing helpers over the records and the connection list",
    "pkg/output.py": "the connection report lists the connection list as written",
    "pkg/store/history.py": "records each instance's connections in the run history",
    "pkg/parser/_syntax_queries/instantiation.py": "extracts connections from the syntax",
}


def _relative(path: Path) -> str:
    return path.relative_to(SRC_ROOT).as_posix()


def _reads_connections(node: ast.AST) -> bool:
    """`x.get("connections", ...)` or `x["connections"]`."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get":
        return bool(node.args) and isinstance(node.args[0], ast.Constant) and node.args[0].value == "connections"
    if isinstance(node, ast.Subscript):
        return isinstance(node.slice, ast.Constant) and node.slice.value == "connections"
    return False


def _offenders() -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for path in sorted(SRC_ROOT.rglob("*.py")):
        rel = _relative(path)
        if rel in CONNECTION_READERS:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        hits: list[str] = []
        for node in ast.walk(tree):
            if _reads_connections(node):
                hits.append(f"line {node.lineno}: reads the raw 'connections' list")
            elif isinstance(node, ast.Name) and node.id in PAIRING_NAMES:
                hits.append(f"line {node.lineno}: uses {node.id}")
            elif isinstance(node, ast.Attribute) and node.attr in PAIRING_NAMES:
                hits.append(f"line {node.lineno}: uses {node.attr}")
            elif isinstance(node, ast.alias) and node.name in PAIRING_NAMES:
                hits.append(f"line {node.lineno}: imports {node.name}")
        if hits:
            found[rel] = hits
    return found


def test_only_listed_files_read_raw_port_connections() -> None:
    offenders = _offenders()
    assert not offenders, (
        "These files read an instance's raw connections or pair ports with connections themselves; use the "
        "ConnectionRecord helpers in rules/connection_analysis.py, or add the file to CONNECTION_READERS with "
        f"the reason: {offenders}"
    )


def test_every_listed_file_exists() -> None:
    missing = [rel for rel in CONNECTION_READERS if not (SRC_ROOT / rel).is_file()]
    assert not missing, f"stale entries in CONNECTION_READERS: {missing}"


def test_the_port_pairing_helper_is_gone() -> None:
    text = (SRC_ROOT / "pkg/rules/connection_analysis.py").read_text(encoding="utf-8")
    assert "def bound_port_pairs" not in text
