"""Per-rule scenario catalog: SystemVerilog snippets with the findings a rule must and must not report.

One file per rule, `tests/scenarios/<rule category>/<RULE_CODE>.sv`. A scenario starts with a marker line and runs to
the next marker:

    // scenario: reports | one sentence on what the rule must catch
    // scenario: clean | one sentence on what the rule must not report (the rule would be too broad)
    // scenario: gap | a case the rule should report but does not yet (the rule is too narrow; strict xfail)

Optional lines directly under the marker: `// pair: <name>` ties a `reports` scenario to the `clean` scenario that
differs from it in the one detail that decides the outcome (a boundary), and `// expect: N` gives the number of
findings of the rule (default 1 for `reports`, 0 for `clean`).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

KINDS = ("reports", "clean", "gap")
SCENARIO_ROOT = Path(__file__).resolve().parents[1] / "scenarios"


@dataclass(frozen=True)
class Scenario:
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


def parse_scenarios(path: Path) -> list[Scenario]:
    rule = path.stem
    scenarios: list[Scenario] = []
    current: dict | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("// scenario:"):
            if current is not None:
                scenarios.append(_finish(rule, current, path))
            kind, _, title = stripped[len("// scenario:"):].partition("|")
            current = {"kind": kind.strip(), "title": title.strip(), "lines": [], "pair": None, "expect": None}
        elif current is not None and stripped.startswith("// pair:") and not current["lines"]:
            current["pair"] = stripped[len("// pair:"):].strip()
        elif current is not None and stripped.startswith("// expect:") and not current["lines"]:
            current["expect"] = int(stripped[len("// expect:"):].strip())
        elif current is not None:
            current["lines"].append(line)
    if current is not None:
        scenarios.append(_finish(rule, current, path))
    return scenarios


def _finish(rule: str, current: dict, path: Path) -> Scenario:
    kind = current["kind"]
    if kind not in KINDS:
        raise ValueError(f"{path}: unknown scenario kind {kind!r}; use one of {KINDS}")
    expect = current["expect"] if current["expect"] is not None else (1 if kind in ("reports", "gap") else 0)
    return Scenario(rule, kind, current["title"], "\n".join(current["lines"]).strip("\n") + "\n", expect, current["pair"], path)


def all_scenario_files() -> list[Path]:
    return sorted(p for p in SCENARIO_ROOT.rglob("*.sv"))


def all_scenarios() -> list[Scenario]:
    return [s for path in all_scenario_files() for s in parse_scenarios(path)]
