"""Meta-tests keeping `pyslang` and raw syntax-node walking behind `pkg.parser`.

Handlers, rules, and the runner ask parser helpers questions about a node
(`subroutine_name(raw)`, `is_in_for_loop_header(raw, ctx)`) rather than reading
`pyslang` fields themselves, so a parser change stays inside `src/pkg/parser/`.
"""
from __future__ import annotations

import ast
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
PKG_ROOT = SRC_ROOT / "pkg"
PARSER_ROOT = PKG_ROOT / "parser"

# Attributes other code may read directly off a vnode's `.raw` node.
ALLOWED_RAW_ATTRIBUTES = {"kind"}

# Modules that wrap `.raw` themselves; their own attribute reads are the boundary.
RAW_WRAPPER_DIRS = (PKG_ROOT / "vnodes",)


def _modules_outside_parser() -> list[Path]:
    return sorted(p for p in SRC_ROOT.rglob("*.py") if PARSER_ROOT not in p.parents)


def _rel(path: Path) -> str:
    return path.relative_to(SRC_ROOT).as_posix()


def test_pyslang_is_imported_only_inside_parser_package() -> None:
    violations: list[str] = []
    for path in _modules_outside_parser():
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            if any(name == "pyslang" or name.startswith("pyslang.") for name in names):
                violations.append(f"{_rel(path)}:{node.lineno}")
    assert not violations, "pyslang imported outside src/pkg/parser/:\n" + "\n".join(violations)


def _find_raw_field_violations(tree: ast.AST, path_label: str) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "raw"
            and node.attr not in ALLOWED_RAW_ATTRIBUTES
        ):
            violations.append(f"{path_label}:{node.lineno}: .raw.{node.attr}")
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        ):
            target = node.args[0]
            attr_name = node.args[1].value
            if (
                isinstance(target, ast.Attribute)
                and target.attr == "raw"
                and attr_name not in ALLOWED_RAW_ATTRIBUTES
            ):
                violations.append(f"{path_label}:{node.lineno}: getattr(.raw, {attr_name!r})")
            elif (
                isinstance(target, ast.Name)
                and target.id in ("raw", "raw_node")
                and attr_name not in ALLOWED_RAW_ATTRIBUTES
            ):
                violations.append(f"{path_label}:{node.lineno}: getattr({target.id}, {attr_name!r})")
    return violations


def test_no_raw_field_walks_outside_parser_package() -> None:
    """`<vnode>.raw.<field>` outside the parser reaches into a pyslang node."""
    violations: list[str] = []
    for path in _modules_outside_parser():
        if any(wrapper in path.parents for wrapper in RAW_WRAPPER_DIRS):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        violations.extend(_find_raw_field_violations(tree, _rel(path)))
    assert not violations, (
        "Raw pyslang field access outside src/pkg/parser/; add a parser helper instead:\n"
        + "\n".join(violations)
    )


def test_raw_field_walker_rejects_raw_getattr_patterns() -> None:
    code = """
def sample_handler(vnode, raw):
    _a = vnode.raw.event
    _b = getattr(vnode.raw, "event", None)
    _c = getattr(raw, "name", None)
    _d = vnode.raw.kind
    _e = getattr(vnode.raw, "kind", None)
"""
    violations = _find_raw_field_violations(ast.parse(code), "sample.py")
    assert len(violations) == 3
    assert any(".raw.event" in v for v in violations)
    assert any("getattr(.raw, 'event')" in v for v in violations)
    assert any("getattr(raw, 'name')" in v for v in violations)
    assert not any("kind" in v for v in violations)



def test_run_lint_parses_only_through_parser_parse_module() -> None:
    """Every `parser` import in run_lint.py comes from `pkg.parser.parse`."""
    tree = ast.parse((SRC_ROOT / "run_lint.py").read_text(encoding="utf-8"))
    parser_imports = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module and ".parser" in f".{node.module}"
    ]
    assert parser_imports, "run_lint.py no longer imports from the parser package"
    offenders = [
        f"run_lint.py:{node.lineno}: from {node.module}"
        for node in parser_imports
        if not node.module.endswith("parser.parse")
    ]
    assert not offenders, "\n".join(offenders)
    imported = {alias.name for node in parser_imports for alias in node.names}
    assert "parse_file" in imported
