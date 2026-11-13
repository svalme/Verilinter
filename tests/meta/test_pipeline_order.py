"""Meta-test fixing the order of the passes in the engine.

A rule or pass that reads data from another phase relies on that phase having run first: the walk of a
file reads the package and module-port registries, the symbol rules read what the instance effects add,
and the module rules read the merged table. Moving a call changes what each of them can see, so the
order is pinned here and described in ARCHITECTURE.md (section 1).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ENGINE = Path(__file__).resolve().parents[2] / "src" / "pkg" / "engine.py"


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    matches = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name]
    assert len(matches) == 1, f"expected one definition of {name}"
    return matches[0]


def _call_lines(func: ast.FunctionDef) -> dict[str, int]:
    """The first line at which each called name appears; an attribute call is keyed by its attribute."""
    lines: dict[str, int] = {}
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        callee = node.func
        name = callee.id if isinstance(callee, ast.Name) else getattr(callee, "attr", None)
        if name is not None and (name not in lines or node.lineno < lines[name]):
            lines[name] = node.lineno
    return lines


def _assert_order(lines: dict[str, int], names: list[str], where: str) -> None:
    missing = [name for name in names if name not in lines]
    assert not missing, f"{where}: no call to {missing}"
    positions = [lines[name] for name in names]
    assert positions == sorted(positions), (
        f"{where}: the calls must run in this order {names}, found lines {dict(zip(names, positions))}. "
        "Update ARCHITECTURE.md section 1 and Docs/PIPELINE_REGISTER.md with the new order."
    )


@pytest.fixture(scope="module")
def engine_tree() -> ast.Module:
    return ast.parse(ENGINE.read_text(encoding="utf-8"))


def test_paths_pipeline_runs_prescans_then_workers_then_merge_then_module_rules(engine_tree: ast.Module) -> None:
    lines = _call_lines(_function(engine_tree, "analyze_paths"))
    _assert_order(
        lines,
        ["_scan_packages", "_scan_module_ports", "_run_workers", "_build_cross_file_symbol_table", "run", "enrich_diagnostics"],
        "analyze_paths",
    )


def test_trees_pipeline_runs_prescans_then_workers_then_merge_then_module_rules(engine_tree: ast.Module) -> None:
    lines = _call_lines(_function(engine_tree, "analyze_trees"))
    _assert_order(
        lines,
        ["_scan_packages_from_trees", "_scan_module_ports_from_trees", "_lint_single_tree", "_build_cross_file_symbol_table", "run"],
        "analyze_trees",
    )


def test_a_file_is_walked_before_instance_effects_and_symbol_rules(engine_tree: ast.Module) -> None:
    lines = _call_lines(_function(engine_tree, "_lint_single_tree"))
    _assert_order(
        lines,
        ["seed_cross_file_packages", "seed_cross_file_module_ports", "walk", "apply_instance_port_effects", "run"],
        "_lint_single_tree",
    )


def test_workers_receive_both_registries(engine_tree: ast.Module) -> None:
    """The worker pool gets the registries as arguments; a worker must not depend on another worker."""
    workers = _function(engine_tree, "_run_workers")
    argument_names = {arg.arg for arg in workers.args.args + workers.args.kwonlyargs}
    assert {"package_registry", "module_ports"} <= argument_names
