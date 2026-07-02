from pathlib import Path
import difflib
import os
import pyslang as sl

from src.pkg.handlers.register_handlers import *
from src.pkg.ast.dispatch import dispatch

from src.pkg.vnodes.syntax_vnode import SyntaxVNode
from src.pkg.ast.walker import Walker
from src.pkg.ast.context import Context
from src.pkg.ast.symbol_table import SymbolTable

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
EXPECTED = ROOT / "expected"
ARTIFACTS = ROOT / "artifacts"  # generated diff output, not source -- gitignored


def print_walk(tree: sl.SyntaxTree) -> str:
    root = SyntaxVNode(tree.root, tree)
    walker = Walker(dispatch)
    symbol_table = SymbolTable()
    walker.walk(root, tree, Context(), symbol_table)

    return "\n".join(repr(vnode) for vnode, _ in walker._results)


def print_snippets(tree: sl.SyntaxTree) -> str:
    root = SyntaxVNode(tree.root, tree)
    walker = Walker(dispatch)
    symbol_table = SymbolTable()
    walker.walk(root, tree, Context(), symbol_table)

    blocks = []
    for vnode, _ in walker._results:
        if isinstance(vnode, SyntaxVNode):
            snippet = vnode.snippet().strip()
            if snippet:
                blocks.append(
                    f"SYNTAXNODE {vnode.raw.kind.name} @ {vnode.location}\n"
                    f"{snippet}\n"
                    f"{'-'*40}"
                )

    return "\n".join(blocks) + "\n"


def normalize(s: str) -> str:
    s = s.replace("\r\n", "\n")
    lines = s.splitlines()
    # drop empty / whitespace-only lines
    lines = [line.rstrip() for line in lines if line.strip() != ""]
    return "\n".join(lines) + "\n"

def html_comparison(s1, s2):
    """
    Generates an HTML file that highlights the differences between two strings.
    """
    diff = difflib.HtmlDiff().make_file(
        s1.splitlines(),
        s2.splitlines(),
        fromdesc='Expected',
        todesc='Actual'
    )
    ARTIFACTS.mkdir(exist_ok=True)
    output_file = ARTIFACTS / "comparison.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(diff)

def assert_matches_expected(name: str, actual: str):
    """Compares `actual` against the golden file `name` in tests/expected/.

    To regenerate a golden file after an intentional output change, run with
    UPDATE_EXPECTED=1 set, e.g.:

        UPDATE_EXPECTED=1 pytest tests/ast/print_tree_test.py

    This overwrites the golden file instead of asserting, so the resulting
    diff (via `git diff`) is a deliberate, reviewable record of what changed
    and why -- rather than a silently stale file the next unrelated change
    trips over.
    """
    expected_file = EXPECTED / name
    actual = normalize(actual)

    if os.environ.get("UPDATE_EXPECTED"):
        expected_file.write_text(actual, encoding="utf-8")
        return

    assert expected_file.exists(), f"Missing expected file: {expected_file}"

    expected = normalize(expected_file.read_text())
    if actual != expected:
        html_comparison(expected, actual)
    assert actual == expected


def test_simple_v():
    tree = sl.SyntaxTree.fromFile(str(DATA / "simple.v"))
    assert_matches_expected("simple.v.walk.txt", print_walk(tree))
    assert_matches_expected("simple.v.snippets.txt", print_snippets(tree))