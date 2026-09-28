"""Meta-tests ensuring static AST recursion safety and traversal depth hygiene.

Uses Python's standard `ast` module to statically inspect all source files under `src/pkg/`:
1. Verifies that every recursive function or method is strictly guarded by either:
   - `@guarded_traversal` or `@guarded_generator` (from `src.pkg.parser.traversal_guard`), OR
   - An explicit `depth` parameter (e.g. `depth: int = 0`) coupled with a depth guard check (`depth >= ...`).
2. Verifies that AST ancestor, child, and scope `while` loops include explicit bounded iteration
   or depth limits (`depth < ...`, `iteration < ...`).
3. Prevents any future pull request or rule implementation from introducing un-guarded recursion
   or unbounded tree/graph traversal loops.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import NamedTuple

import pytest

pytestmark = pytest.mark.meta

SRC_PKG_DIR = Path(__file__).resolve().parents[2] / "src" / "pkg"


class RecursiveFunctionRecord(NamedTuple):
    file: str
    line: int
    name: str
    has_guard_decorator: bool
    has_depth_guard: bool


def _is_call_to_func(call_node: ast.Call, func_name: str, in_class: bool) -> bool:
    """Checks whether an AST Call node targets `func_name` or `self.func_name`."""
    if isinstance(call_node.func, ast.Name) and call_node.func.id == func_name:
        return True
    if in_class and isinstance(call_node.func, ast.Attribute) and call_node.func.attr == func_name:
        if isinstance(call_node.func.value, ast.Name) and call_node.func.value.id in ("self", "cls"):
            return True
    return False


def _find_imported_symbols(tree: ast.AST) -> set[str]:
    """Collects all explicitly imported symbol names in the module to avoid false recursion positives."""
    imported = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.asname or alias.name)
    return imported


def _has_depth_check(fn_node: ast.FunctionDef | ast.AsyncFunctionDef, depth_arg_name: str) -> bool:
    """Checks whether the function body contains a comparison or condition on the depth argument."""
    for node in ast.walk(fn_node):
        if isinstance(node, ast.Compare):
            unparsed = ast.unparse(node).lower()
            if depth_arg_name.lower() in unparsed:
                return True
        elif isinstance(node, ast.If):
            unparsed = ast.unparse(node.test).lower()
            if depth_arg_name.lower() in unparsed:
                return True
    return False


class FunctionVisitor(ast.NodeVisitor):
    def __init__(self, imported_names: set[str], rel_path: str) -> None:
        self.imported_names = imported_names
        self.rel_path = rel_path
        self.records: list[RecursiveFunctionRecord] = []
        self.class_stack: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_fn(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_fn(node)
        self.generic_visit(node)

    def _check_fn(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        fn_name = node.name
        in_class = bool(self.class_stack)

        # If a method shares a name with an imported function (e.g. identifier_name),
        # calls to identifier_name(...) are external calls, not self-recursion.
        if in_class and fn_name in self.imported_names:
            calls_self = any(
                isinstance(inner, ast.Call)
                and isinstance(inner.func, ast.Attribute)
                and inner.func.attr == fn_name
                and isinstance(inner.func.value, ast.Name)
                and inner.func.value.id in ("self", "cls")
                for inner in ast.walk(node)
                if inner is not node
            )
        else:
            calls_self = any(
                isinstance(inner, ast.Call) and _is_call_to_func(inner, fn_name, in_class)
                for inner in ast.walk(node)
                if inner is not node
            )

        if not calls_self:
            return

        # Check for guard decorators
        decorator_names: list[str] = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorator_names.append(dec.id)
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    decorator_names.append(dec.func.id)
                elif isinstance(dec.func, ast.Attribute):
                    decorator_names.append(dec.func.attr)

        has_guard_decorator = any("guarded" in d for d in decorator_names)

        # Check for depth parameter and check in body
        depth_args = [a.arg for a in node.args.args if "depth" in a.arg.lower()]
        has_depth_guard = False
        if depth_args:
            has_depth_guard = any(_has_depth_check(node, d_arg) for d_arg in depth_args)

        self.records.append(
            RecursiveFunctionRecord(
                file=self.rel_path,
                line=node.lineno,
                name=fn_name,
                has_guard_decorator=has_guard_decorator,
                has_depth_guard=has_depth_guard,
            )
        )


def _inspect_functions_in_tree(tree: ast.AST, rel_path: str) -> list[RecursiveFunctionRecord]:
    """Scans an AST tree for recursive functions and evaluates their safety guards."""
    imported_names = _find_imported_symbols(tree)
    visitor = FunctionVisitor(imported_names, rel_path)
    visitor.visit(tree)
    return visitor.records


def test_all_recursive_functions_are_guarded() -> None:
    """Verifies every recursive function in `src/pkg/` is guarded against cycles and recursion depth."""
    violations: list[str] = []
    scanned_count = 0

    for py_file in sorted(SRC_PKG_DIR.rglob("*.py")):
        rel_path = str(py_file.relative_to(SRC_PKG_DIR))
        with open(py_file, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=str(py_file))
            except Exception as e:
                violations.append(f"{rel_path}: Failed to parse AST: {e}")
                continue

        records = _inspect_functions_in_tree(tree, rel_path)
        for rec in records:
            scanned_count += 1
            if not rec.has_guard_decorator and not rec.has_depth_guard:
                violations.append(
                    f"{rec.file}:{rec.line} - Recursive function `{rec.name}` lacks a safety guard! "
                    f"Must be decorated with `@guarded_traversal`/`@guarded_generator` or specify "
                    f"a bounded `depth` parameter (e.g. `depth: int = 0` with `depth >= MAX_DEPTH`)."
                )

    assert not violations, (
        f"Found {len(violations)} un-guarded recursive functions in src/pkg:\n"
        + "\n".join(f"  - {v}" for v in violations)
    )
    # Ensure our check actively found and verified the codebase's recursive functions
    assert scanned_count >= 20, f"Expected to audit at least 20 recursive functions, found {scanned_count}"


def test_all_ast_traversal_while_loops_are_bounded() -> None:
    """Verifies that while loops in `src/pkg/` walking AST/graphs have explicit depth or iteration limits."""
    # Whitelist for non-AST scalar while loops
    ALLOWLIST_WHILE_LOOPS = {
        ("engine.py", "True"),  # substring position search advancing pos = text.find()
        ("analysis_store.py", "version != SCHEMA_VERSION"),  # SQLite schema step migration
        ("parser/traversal_guard.py", "stack"),  # Iterative stack DFS popping each step
        ("parser\\traversal_guard.py", "stack"),
    }

    violations: list[str] = []

    for py_file in sorted(SRC_PKG_DIR.rglob("*.py")):
        rel_path = str(py_file.relative_to(SRC_PKG_DIR))
        with open(py_file, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=str(py_file))
            except Exception:
                continue

        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                test_str = ast.unparse(node.test)
                if (rel_path, test_str) in ALLOWLIST_WHILE_LOOPS or (rel_path.replace("/", "\\"), test_str) in ALLOWLIST_WHILE_LOOPS:
                    continue

                # Check if loop test condition contains bounding variables or comparisons
                has_bound = any(
                    marker in test_str.lower()
                    for marker in ("depth", "iter", "count", "len(", "<", ">")
                )
                if not has_bound:
                    violations.append(
                        f"{rel_path}:{node.lineno} - `while {test_str}` loop lacks an explicit depth/iteration bound!"
                    )

    assert not violations, (
        f"Found {len(violations)} un-bounded while loops in src/pkg:\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


def test_meta_checker_detects_synthetic_unguarded_recursion() -> None:
    """Meta-validation: verifies that _inspect_functions_in_tree reliably flags unguarded recursions."""
    bad_code = """
def bad_walk(node):
    if node:
        bad_walk(node.left)
"""
    tree = ast.parse(bad_code)
    records = _inspect_functions_in_tree(tree, "synthetic.py")
    assert len(records) == 1
    assert records[0].name == "bad_walk"
    assert records[0].has_guard_decorator is False
    assert records[0].has_depth_guard is False

    good_guarded_code = """
@guarded_traversal(max_depth=64)
def good_walk(node):
    if node:
        good_walk(node.left)
"""
    tree_good = ast.parse(good_guarded_code)
    records_good = _inspect_functions_in_tree(tree_good, "synthetic.py")
    assert len(records_good) == 1
    assert records_good[0].has_guard_decorator is True

    good_depth_code = """
def good_depth_walk(node, depth: int = 0):
    if depth >= 64:
        return
    if node:
        good_depth_walk(node.left, depth + 1)
"""
    tree_depth = ast.parse(good_depth_code)
    records_depth = _inspect_functions_in_tree(tree_depth, "synthetic.py")
    assert len(records_depth) == 1
    assert records_depth[0].has_depth_guard is True
