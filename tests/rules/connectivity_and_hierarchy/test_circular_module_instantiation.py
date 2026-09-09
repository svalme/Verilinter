import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.connectivity_and_hierarchy.circular_module_instantiation import CircularModuleInstantiationRule
from tests.support.parse_diagnostics import assert_no_parse_errors


SELF_INSTANTIATION_CODE = """
module top;
  top u_top();
endmodule
"""

TWO_MODULE_CYCLE_CODE = """
module a;
  b u_b();
endmodule

module b;
  a u_a();
endmodule
"""

THREE_MODULE_CYCLE_CODE = """
module a;
  b u_b();
endmodule

module b;
  c u_c();
endmodule

module c;
  a u_a();
endmodule
"""

NO_CYCLE_CODE = """
module top;
  leaf u_leaf();
endmodule

module leaf;
endmodule
"""

DIAMOND_NO_CYCLE_CODE = """
module top;
  left u_left();
  right u_right();
endmodule

module left;
  shared_leaf u_leaf();
endmodule

module right;
  shared_leaf u_leaf();
endmodule

module shared_leaf;
endmodule
"""


class TestCircularModuleInstantiationRule:
    @pytest.fixture
    def rule(self) -> CircularModuleInstantiationRule:
        return CircularModuleInstantiationRule()

    def test_rule_has_correct_code(self, rule: CircularModuleInstantiationRule) -> None:
        assert rule.code == "CIRCULAR_MODULE_INSTANTIATION"

    def test_flags_direct_self_instantiation(self, rule: CircularModuleInstantiationRule) -> None:
        st = SymbolTable()
        st.register_instantiation_edge("top", "top", {"line": 3, "col": 3, "file": "a.v"})

        diagnostics = rule.run(st)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "CIRCULAR_MODULE_INSTANTIATION"
        assert diagnostics[0]["line"] == 3
        assert "top" in diagnostics[0]["message"]

    def test_flags_two_module_cycle(self, rule: CircularModuleInstantiationRule) -> None:
        st = SymbolTable()
        st.register_instantiation_edge("a", "b", {"line": 2, "col": 3, "file": "x.v"})
        st.register_instantiation_edge("b", "a", {"line": 6, "col": 3, "file": "x.v"})

        diagnostics = rule.run(st)

        assert len(diagnostics) == 1
        assert "a" in diagnostics[0]["message"]
        assert "b" in diagnostics[0]["message"]

    def test_does_not_flag_acyclic_graph(self, rule: CircularModuleInstantiationRule) -> None:
        st = SymbolTable()
        st.register_instantiation_edge("top", "leaf", {"line": 2, "col": 3, "file": "x.v"})

        assert rule.run(st) == []

    def test_does_not_flag_diamond_shaped_hierarchy(self, rule: CircularModuleInstantiationRule) -> None:
        """top -> left -> shared_leaf and top -> right -> shared_leaf is not a cycle,
        even though shared_leaf is reachable from top via two different paths."""
        st = SymbolTable()
        st.register_instantiation_edge("top", "left", {"line": 2, "col": 3, "file": "x.v"})
        st.register_instantiation_edge("top", "right", {"line": 3, "col": 3, "file": "x.v"})
        st.register_instantiation_edge("left", "shared_leaf", {"line": 7, "col": 3, "file": "x.v"})
        st.register_instantiation_edge("right", "shared_leaf", {"line": 11, "col": 3, "file": "x.v"})

        assert rule.run(st) == []

    def test_no_edges_returns_no_diagnostics(self, rule: CircularModuleInstantiationRule) -> None:
        assert rule.run(SymbolTable()) == []

    def test_against_real_parsed_source_self_instantiation(self, rule: CircularModuleInstantiationRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(SELF_INSTANTIATION_CODE)
        assert_no_parse_errors("tests/rules/connectivity_and_hierarchy/test_circular_module_instantiation.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert "top" in diagnostics[0]["message"]

    def test_against_real_parsed_source_two_module_cycle(self, rule: CircularModuleInstantiationRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(TWO_MODULE_CYCLE_CODE)
        assert_no_parse_errors("tests/rules/connectivity_and_hierarchy/test_circular_module_instantiation.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert "a" in diagnostics[0]["message"]
        assert "b" in diagnostics[0]["message"]

    def test_against_real_parsed_source_three_module_cycle(self, rule: CircularModuleInstantiationRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(THREE_MODULE_CYCLE_CODE)
        assert_no_parse_errors("tests/rules/connectivity_and_hierarchy/test_circular_module_instantiation.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        for name in ("a", "b", "c"):
            assert name in diagnostics[0]["message"]

    def test_against_real_parsed_source_no_cycle(self, rule: CircularModuleInstantiationRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(NO_CYCLE_CODE)
        assert_no_parse_errors("tests/rules/connectivity_and_hierarchy/test_circular_module_instantiation.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_against_real_parsed_source_diamond_no_cycle(self, rule: CircularModuleInstantiationRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(DIAMOND_NO_CYCLE_CODE)
        assert_no_parse_errors("tests/rules/connectivity_and_hierarchy/test_circular_module_instantiation.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []
