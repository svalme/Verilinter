from src.pkg.handlers.register_handlers import *
from src.pkg.parser.parse import parse_text
from src.pkg.rules.parameters_and_generate_logic.unknown_named_parameter_override import UnknownNamedParameterOverrideRule
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/parameters_and_generate_logic/test_unknown_named_parameter_override.py", tree)
    Walker(dispatch).walk(tree.root, tree, Context(scope=symbol_table.global_scope), symbol_table)
    return UnknownNamedParameterOverrideRule().run(symbol_table)


CHILD = """
module child #(parameter int W = 1, parameter type data_t = logic) (input data_t d_i);
endmodule
"""


class TestUnknownNamedParameterOverrideRule:
    def test_type_parameter_override_is_known(self) -> None:
        code = CHILD + """
module top (input logic d);
  child #(.W(2), .data_t(logic)) u (.d_i(d));
endmodule
"""
        assert _diagnostics(code) == []

    def test_name_that_is_neither_value_nor_type_parameter_is_flagged(self) -> None:
        code = CHILD + """
module top (input logic d);
  child #(.W(2), .data_t(logic), .Bogus(1)) u (.d_i(d));
endmodule
"""
        diags = _diagnostics(code)
        assert len(diags) == 1
        assert diags[0]["message"].endswith("Bogus")
