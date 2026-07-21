from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULES_ROOT = ROOT / "src" / "pkg" / "rules"
HANDLERS_ROOT = ROOT / "src" / "pkg" / "handlers"


def _imported_module_stems(register_file: Path, relative_prefix: str) -> set[str]:
    tree = ast.parse(register_file.read_text(encoding="utf-8"))
    stems: set[str] = set()

    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module is None or not node.module.startswith(relative_prefix):
            continue
        stems.add(node.module.split(".")[-1])

    return stems


def _python_module_stems(directory: Path, excluded: set[str]) -> set[str]:
    return {
        path.stem
        for path in directory.glob("*.py")
        if path.stem not in excluded
    }


def test_register_rules_imports_all_rule_modules() -> None:
    register_file = RULES_ROOT / "register_rules.py"

    imported_syntax = _imported_module_stems(register_file, "syntax.")
    imported_symbol = _imported_module_stems(register_file, "symbol.")
    imported_module = _imported_module_stems(register_file, "module.")

    expected_syntax = _python_module_stems(
        RULES_ROOT / "syntax",
        excluded={"__init__", "rule_runner"},
    )
    expected_symbol = _python_module_stems(
        RULES_ROOT / "symbol",
        excluded={"__init__", "symbol_rule_runner"},
    )
    expected_module = _python_module_stems(
        RULES_ROOT / "module",
        excluded={"__init__", "module_rule_runner"},
    )

    imported_syntax.discard("rule_runner")
    imported_symbol.discard("symbol_rule_runner")
    imported_module.discard("module_rule_runner")
    assert imported_syntax == expected_syntax
    assert imported_symbol == expected_symbol
    assert imported_module == expected_module


def test_register_handlers_imports_all_handler_modules() -> None:
    register_file = HANDLERS_ROOT / "register_handlers.py"
    imported_handlers = _imported_module_stems(register_file, "")

    expected_handlers = _python_module_stems(
        HANDLERS_ROOT,
        excluded={"__init__", "register_handlers", "base_handler", "syntax_node_handler", "token_handler"},
    )

    imported_handlers.discard("dispatch")
    imported_handlers.discard("syntax_node_handler")
    imported_handlers.discard("token_handler")
    assert imported_handlers == expected_handlers
