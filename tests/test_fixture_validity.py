"""Every checked-in fixture in tests/data/ should parse as valid SystemVerilog.

Fixtures are heavily reused (some by a dozen or more test files), so a fixture
with a real syntax error silently corrupts every test that parses it -- pyslang's
error recovery produces *some* AST, which can make an assertion pass for reasons
unrelated to the RTL the fixture is supposed to demonstrate.

A fixture that intentionally exercises parser recovery belongs in
INTENTIONAL_PARSE_ERROR_FIXTURES with a comment explaining what it demonstrates,
not silently passing this check.
"""

from pathlib import Path

import pyslang as sl
import pytest

DATA = Path(__file__).parent / "data"

# Fixtures listed here are *expected* to fail to parse cleanly, and this test
# skips them instead of asserting a clean parse. Nothing is listed today: every
# fixture parses cleanly.
INTENTIONAL_PARSE_ERROR_FIXTURES: frozenset[str] = frozenset()

FIXTURE_PATHS = sorted(
    path for path in DATA.iterdir() if path.is_file() and path.suffix in (".v", ".sv")
)


def _render_diagnostics(tree: sl.SyntaxTree) -> str:
    engine = sl.DiagnosticEngine(tree.sourceManager)
    client = sl.TextDiagnosticClient()
    engine.addClient(client)
    for diagnostic in tree.diagnostics:
        engine.issue(diagnostic)
    return client.getString()


@pytest.mark.parametrize("path", FIXTURE_PATHS, ids=lambda p: p.name)
def test_fixture_parses_without_errors(path: Path) -> None:
    if path.name in INTENTIONAL_PARSE_ERROR_FIXTURES:
        pytest.skip(f"{path.name} intentionally exercises parser recovery")

    tree = sl.SyntaxTree.fromFile(str(path))
    errors = [d for d in tree.diagnostics if d.isError]

    assert not errors, (
        f"{path.name} has real syntax errors; either fix the fixture or add it "
        f"to INTENTIONAL_PARSE_ERROR_FIXTURES with a comment explaining why:\n"
        f"{_render_diagnostics(tree)}"
    )


def test_intentional_parse_error_fixtures_still_exist() -> None:
    """Catches an allowlist entry going stale after a fixture is renamed/removed."""
    fixture_names = {path.name for path in FIXTURE_PATHS}
    missing = INTENTIONAL_PARSE_ERROR_FIXTURES - fixture_names
    assert not missing, f"Allowlisted fixtures no longer exist: {missing}"
