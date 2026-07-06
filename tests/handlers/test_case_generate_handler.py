import pyslang as sl
import pytest

from src.pkg.walk.context import Context, ContextFlag
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.vnodes.base_vnode import BaseVNode
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.syntax.default_case import DefaultCaseRule

WITH_DEFAULT = """
module m;
  generate
    case (1)
      0: begin
        wire a;
      end
      default: begin
        wire b;
      end
    endcase
  endgenerate
endmodule
"""

WITHOUT_DEFAULT = """
module m;
  generate
    case (1)
      0: begin
        wire a;
      end
    endcase
  endgenerate
endmodule
"""


def _endcase_node(code: str) -> tuple[BaseVNode, Context]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    for vnode, node_ctx in walker.results:
        if vnode.raw.kind == sl.TokenKind.EndCaseKeyword:
            return vnode, node_ctx

    raise AssertionError("no EndCaseKeyword token found in walk results")


class TestCaseGenerateHandler:
    def test_sets_default_flag_when_default_item_present(self) -> None:
        _, ctx = _endcase_node(WITH_DEFAULT)

        assert ctx.has(ContextFlag.CASE_GENERATE)
        assert ctx.has(ContextFlag.DEFAULT)

    def test_does_not_set_default_flag_when_default_item_absent(self) -> None:
        _, ctx = _endcase_node(WITHOUT_DEFAULT)

        assert ctx.has(ContextFlag.CASE_GENERATE)
        assert not ctx.has(ContextFlag.DEFAULT)

    def test_default_case_rule_does_not_fire_when_default_present(self) -> None:
        vnode, ctx = _endcase_node(WITH_DEFAULT)

        assert DefaultCaseRule().applies(vnode, ctx) is False

    def test_default_case_rule_fires_when_default_absent(self) -> None:
        vnode, ctx = _endcase_node(WITHOUT_DEFAULT)

        assert DefaultCaseRule().applies(vnode, ctx) is True
