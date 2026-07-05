import pytest

from src.pkg.ast.symbol_table import SymbolTable
from src.pkg.rules.module.duplicate_module_definition import DuplicateModuleDefinitionRule


class TestDuplicateModuleDefinitionRule:
    """Test cases for the DuplicateModuleDefinitionRule."""

    @pytest.fixture
    def rule(self) -> DuplicateModuleDefinitionRule:
        return DuplicateModuleDefinitionRule()

    def test_rule_has_correct_code(self, rule: DuplicateModuleDefinitionRule) -> None:
        assert rule.code == "DUPLICATE_MODULE"

    def test_no_diagnostics_for_single_definition(self, rule: DuplicateModuleDefinitionRule) -> None:
        st = SymbolTable()
        st.set_current_file("a.v")
        scope = st.new_scope(kind="module", name="foo", location={"line": 1, "col": 1, "file": "a.v"})
        st.register_module("foo", scope)

        assert rule.run(st) == []

    def test_flags_duplicate_module_with_second_location(self, rule: DuplicateModuleDefinitionRule) -> None:
        st = SymbolTable()
        st.set_current_file("a.v")
        s1 = st.new_scope(kind="module", name="foo", location={"line": 1, "col": 1, "file": "a.v"})
        st.register_module("foo", s1)
        st.pop_scope()

        st.set_current_file("b.v")
        s2 = st.new_scope(kind="module", name="foo", location={"line": 3, "col": 1, "file": "b.v"})
        st.register_module("foo", s2)

        diagnostics = rule.run(st)

        assert len(diagnostics) == 1
        assert diagnostics[0]["line"] == 3
        assert diagnostics[0]["col"] == 1
        assert diagnostics[0]["file"] == "b.v"
        assert "foo" in diagnostics[0]["message"]
        assert "a.v" in diagnostics[0]["message"]

    def test_three_definitions_flags_second_and_third_only(self, rule: DuplicateModuleDefinitionRule) -> None:
        st = SymbolTable()
        for path in ("a.v", "b.v", "c.v"):
            st.set_current_file(path)
            scope = st.new_scope(kind="module", name="foo", location={"line": 1, "col": 1, "file": path})
            st.register_module("foo", scope)
            st.pop_scope()

        diagnostics = rule.run(st)
        assert len(diagnostics) == 2
        assert {d["file"] for d in diagnostics} == {"b.v", "c.v"}

    def test_different_module_names_not_flagged(self, rule: DuplicateModuleDefinitionRule) -> None:
        st = SymbolTable()
        st.set_current_file("a.v")
        s1 = st.new_scope(kind="module", name="foo", location={"line": 1, "col": 1, "file": "a.v"})
        st.register_module("foo", s1)
        st.pop_scope()

        st.set_current_file("b.v")
        s2 = st.new_scope(kind="module", name="bar", location={"line": 1, "col": 1, "file": "b.v"})
        st.register_module("bar", s2)

        assert rule.run(st) == []

    def test_no_modules_returns_no_diagnostics(self, rule: DuplicateModuleDefinitionRule) -> None:
        st = SymbolTable()
        assert rule.run(st) == []
