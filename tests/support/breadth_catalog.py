"""Per-rule breadth catalog: SystemVerilog snippets with the findings a rule must and must not report.

One file per rule, `tests/breadth/<rule category>/<RULE_CODE>.sv`. A breadth case starts with a marker line and runs to
the next marker:

    // breadth: reports | one sentence on what the rule must catch
    // breadth: clean | one sentence on what the rule must not report (the rule would be too broad)
    // breadth: gap | a breadth case the rule should report but does not yet (the rule is too narrow; strict xfail)

Optional lines directly under the marker: `// pair: <name>` ties a `reports` breadth case to the `clean` breadth case that
differs from it in the one detail that decides the outcome (a boundary), and `// expect: N` gives the number of
findings of the rule (default 1 for `reports`, 0 for `clean`).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

KINDS = ("reports", "clean", "gap")
BREADTH_ROOT = Path(__file__).resolve().parents[1] / "breadth"


@dataclass(frozen=True)
class BreadthCase:
    rule: str
    kind: str
    title: str
    source: str
    expect: int
    pair: str | None
    path: Path

    @property
    def id(self) -> str:
        return f"{self.rule}::{self.kind}::{self.title[:60]}"


def parse_breadth_cases(path: Path) -> list[BreadthCase]:
    rule = path.stem
    breadth_cases: list[BreadthCase] = []
    current: dict | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("// breadth:"):
            if current is not None:
                breadth_cases.append(_finish(rule, current, path))
            kind, _, title = stripped[len("// breadth:"):].partition("|")
            current = {"kind": kind.strip(), "title": title.strip(), "lines": [], "pair": None, "expect": None}
        elif current is not None and stripped.startswith("// pair:") and not current["lines"]:
            current["pair"] = stripped[len("// pair:"):].strip()
        elif current is not None and stripped.startswith("// expect:") and not current["lines"]:
            current["expect"] = int(stripped[len("// expect:"):].strip())
        elif current is not None:
            current["lines"].append(line)
    if current is not None:
        breadth_cases.append(_finish(rule, current, path))
    return breadth_cases


def _finish(rule: str, current: dict, path: Path) -> BreadthCase:
    kind = current["kind"]
    if kind not in KINDS:
        raise ValueError(f"{path}: unknown breadth case kind {kind!r}; use one of {KINDS}")
    expect = current["expect"] if current["expect"] is not None else (1 if kind in ("reports", "gap") else 0)
    return BreadthCase(rule, kind, current["title"], "\n".join(current["lines"]).strip("\n") + "\n", expect, current["pair"], path)


def all_breadth_files() -> list[Path]:
    return sorted(p for p in BREADTH_ROOT.rglob("*.sv"))


def all_breadth_cases() -> list[BreadthCase]:
    return [s for path in all_breadth_files() for s in parse_breadth_cases(path)]
