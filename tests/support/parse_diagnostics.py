"""Shared helpers for checking pyslang parse results for real syntax errors.

pyslang's parser recovers from most syntax errors and still returns a usable
(but corrupted) AST. Any test path that hands source text to pyslang -- the
shared lint harness, fixture validity checks, or a rule test's own bespoke
inline-parsing helper -- can silently pass for reasons unrelated to the RTL
it's supposed to demonstrate unless it explicitly checks `tree.diagnostics`
first.
"""

from __future__ import annotations

import pyslang as sl


def render_diagnostics(tree: sl.SyntaxTree) -> str:
    engine = sl.DiagnosticEngine(tree.sourceManager)
    client = sl.TextDiagnosticClient()
    engine.addClient(client)
    for diagnostic in tree.diagnostics:
        engine.issue(diagnostic)
    return client.getString()


def parse_errors(tree: sl.SyntaxTree) -> list[object]:
    """Return the subset of `tree.diagnostics` that are real errors (not warnings)."""
    return [d for d in tree.diagnostics if d.isError()]


def assert_no_parse_errors(label: str, tree: sl.SyntaxTree) -> None:
    """Raise with a rendered diagnostic dump if `tree` has real parser errors.

    `label` identifies the source to the failing test -- a file path for a
    checked-in fixture, or a synthetic name for an inline snippet.
    """
    errors = parse_errors(tree)
    assert not errors, (
        f"{label} has real syntax errors; either fix the snippet/fixture or "
        f"opt in to expecting parse errors and assert on them explicitly:\n"
        f"{render_diagnostics(tree)}"
    )


__all__ = ["assert_no_parse_errors", "parse_errors", "render_diagnostics"]
