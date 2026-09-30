import pyslang as sl
import pytest

from src.pkg.handlers.register_handlers import *
from src.pkg.parser.syntax import branch_exclusivity_signature, is_mutually_exclusive_branch_pair
from src.pkg.rules.combinational_logic.no_multiple_drivers import NoMultipleDriversRule
from src.pkg.rules.connectivity_and_hierarchy.instance_output_driver_conflict import (
    InstanceOutputDriverConflictRule,
)
from src.pkg.rules.connectivity_and_hierarchy.multiple_instance_driver_conflict import (
    MultipleInstanceDriverConflictRule,
)
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.parse_diagnostics import assert_no_parse_errors


def test_deterministic_construct_identity_across_independent_trees() -> None:
    """Verifies Action Item 2.4: signatures produce identical location-based construct
    identities across independently parsed syntax trees at the same source position."""
    source = """
    module m;
      initial begin
        case (sel)
          1: a = 1;
          default: a = 2;
        endcase
      end
    endmodule
    """
    tree1 = sl.SyntaxTree.fromText(source)
    tree2 = sl.SyntaxTree.fromText(source)

    case1 = tree1.root.members[0].statement.items[0]
    case2 = tree2.root.members[0].statement.items[0]

    node1 = case1.items[0].clause.expr.left
    node2 = case2.items[0].clause.expr.left

    sig1 = branch_exclusivity_signature(node1, tree1)
    sig2 = branch_exclusivity_signature(node2, tree2)

    assert sig1 == sig2
    # Ensure it is a deterministic location string, not an integer id
    assert isinstance(sig1[0][0], str)
    assert ":" in sig1[0][0]
    assert sig1[0][1] == 0


_MACRO_SOURCE = """
`define SEL(a, b) if (c) a = 1; else b = 1;
module m(input c, output reg x, y, z, w);
  always @* begin
    `SEL(x, y) `SEL(z, w)
  end
endmodule
"""


def _signatures_by_name(tree: sl.SyntaxTree, names: tuple[str, ...]) -> dict[str, tuple]:
    found: dict[str, tuple] = {}

    def visit(node: sl.SyntaxNode) -> None:
        if node.kind == sl.SyntaxKind.IdentifierName and str(node).strip() in names:
            found[str(node).strip()] = branch_exclusivity_signature(node, tree)
        for child in node:
            if isinstance(child, sl.SyntaxNode):
                visit(child)

    visit(tree.root)
    return found


def test_macro_expansions_on_one_line_get_distinct_construct_identities() -> None:
    """Two expansions of one macro on the same source line are separate constructs,
    so a branch taken in one is not mutually exclusive with a branch taken in the other."""
    sigs = _signatures_by_name(sl.SyntaxTree.fromText(_MACRO_SOURCE), ("x", "y", "z", "w"))

    assert is_mutually_exclusive_branch_pair(sigs["x"], sigs["y"])
    assert is_mutually_exclusive_branch_pair(sigs["z"], sigs["w"])
    assert not is_mutually_exclusive_branch_pair(sigs["x"], sigs["w"])
    assert not is_mutually_exclusive_branch_pair(sigs["y"], sigs["z"])
    assert sigs["x"][0][0] != sigs["z"][0][0]


def test_macro_construct_identity_is_deterministic_across_independent_trees() -> None:
    names = ("x", "y", "z", "w")
    first = _signatures_by_name(sl.SyntaxTree.fromText(_MACRO_SOURCE), names)
    second = _signatures_by_name(sl.SyntaxTree.fromText(_MACRO_SOURCE), names)

    assert first == second


def test_construct_identity_without_a_tree_does_not_collide_across_constructs() -> None:
    """With no tree there is no file to key on, so two constructs at the same buffer
    offset in different files must still get different identities."""
    source = """
    module m;
      initial begin
        if (a) x = 1; else x = 2;
      end
    endmodule
    """
    first = sl.SyntaxTree.fromText(source)
    second = sl.SyntaxTree.fromText(source)
    node1 = first.root.members[0].statement.items[0].statement.expr.left
    node2 = second.root.members[0].statement.items[0].statement.expr.left

    assert branch_exclusivity_signature(node1) != branch_exclusivity_signature(node2)


def test_procedural_case_branches_are_mutually_exclusive() -> None:
    """Verifies Action Item 2.5: distinct branches of a procedural case statement
    have mutually exclusive branch signatures."""
    source = """
    module m;
      initial begin
        case (sel)
          2'b00: a = 1;
          2'b01: a = 2;
          default: a = 3;
        endcase
      end
    endmodule
    """
    tree = sl.SyntaxTree.fromText(source)
    case_stmt = tree.root.members[0].statement.items[0]

    a0 = case_stmt.items[0].clause.expr.left
    a1 = case_stmt.items[1].clause.expr.left
    a2 = case_stmt.items[2].clause.expr.left

    sig0 = branch_exclusivity_signature(a0, tree)
    sig1 = branch_exclusivity_signature(a1, tree)
    sig2 = branch_exclusivity_signature(a2, tree)

    assert sig0[0][1] == 0
    assert sig1[0][1] == 1
    assert sig2[0][1] == 2

    assert is_mutually_exclusive_branch_pair(sig0, sig1)
    assert is_mutually_exclusive_branch_pair(sig0, sig2)
    assert is_mutually_exclusive_branch_pair(sig1, sig2)
    assert not is_mutually_exclusive_branch_pair(sig0, sig0)


def test_generate_case_different_branches_do_not_flag_multiple_drivers() -> None:
    """Two continuous assigns in mutually exclusive generate-case branches must not
    flag NO_MULTIPLE_DRIVERS."""
    source = """
    module top #(parameter MODE = 0) (input logic a, input logic b, output logic x);
      generate
        case (MODE)
          0: assign x = a;
          1: assign x = b;
          default: assign x = 1'b0;
        endcase
      endgenerate
    endmodule
    """
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(source)
    assert_no_parse_errors("test_generate_case_different_branches_do_not_flag_multiple_drivers", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    rule = NoMultipleDriversRule()
    diagnostics = rule.run(symbol_table)
    assert diagnostics == []


def test_generate_case_same_branch_flags_multiple_drivers() -> None:
    """Negative control: two continuous assigns in the same generate-case branch
    must still flag NO_MULTIPLE_DRIVERS."""
    source = """
    module top #(parameter MODE = 0) (input logic a, input logic b, output logic x);
      generate
        case (MODE)
          0: begin
            assign x = a;
            assign x = b;
          end
          default: assign x = 1'b0;
        endcase
      endgenerate
    endmodule
    """
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(source)
    assert_no_parse_errors("test_generate_case_same_branch_flags_multiple_drivers", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    rule = NoMultipleDriversRule()
    diagnostics = rule.run(symbol_table)
    assert len(diagnostics) == 1
    assert diagnostics[0]["code"] == "NO_MULTIPLE_DRIVERS"


def test_generate_case_instance_driver_conflict_suppressed() -> None:
    """Two instantiations driving the same net in mutually exclusive generate-case branches
    must not flag MULTIPLE_INSTANCE_DRIVER_CONFLICT."""
    source = """
    module sub(output logic out);
      assign out = 1'b1;
    endmodule

    module top #(parameter CFG = 0);
      wire sig;
      generate
        case (CFG)
          0: sub u_sub0 (.out(sig));
          1: sub u_sub1 (.out(sig));
          default: sub u_sub_def (.out(sig));
        endcase
      endgenerate
    endmodule
    """
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(source)
    assert_no_parse_errors("test_generate_case_instance_driver_conflict_suppressed", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    rule = MultipleInstanceDriverConflictRule()
    diagnostics = rule.run(symbol_table)
    assert diagnostics == []


def test_generate_case_instance_driver_conflict_same_branch_flags() -> None:
    """Negative control: two instantiations driving the same net in the same generate-case
    branch must flag MULTIPLE_INSTANCE_DRIVER_CONFLICT."""
    source = """
    module sub(output logic out);
      assign out = 1'b1;
    endmodule

    module top #(parameter CFG = 0);
      wire sig;
      generate
        case (CFG)
          0: begin
            sub u_sub0 (.out(sig));
            sub u_sub1 (.out(sig));
          end
        endcase
      endgenerate
    endmodule
    """
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(source)
    assert_no_parse_errors("test_generate_case_instance_driver_conflict_same_branch_flags", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    rule = MultipleInstanceDriverConflictRule()
    diagnostics = rule.run(symbol_table)
    assert len(diagnostics) == 1
    assert diagnostics[0]["code"] == "MULTIPLE_INSTANCE_DRIVER_CONFLICT"


def test_nested_if_and_case_branch_exclusivity() -> None:
    """Arbitrary nesting of `if`/`else` and `case` constructs must properly track
    ancestor branches and detect mutual exclusivity at both construct levels."""
    source = """
    module top;
      initial begin
        if (cond) begin
          case (sel)
            1: a = 1;
            2: a = 2;
          endcase
        end else begin
          a = 3;
        end
      end
    endmodule
    """
    tree = sl.SyntaxTree.fromText(source)
    if_stmt = tree.root.members[0].statement.items[0]
    case_stmt = if_stmt.statement.items[0]

    a1 = case_stmt.items[0].clause.expr.left
    a2 = case_stmt.items[1].clause.expr.left
    a3 = if_stmt.elseClause.clause.items[0].expr.left

    sig1 = branch_exclusivity_signature(a1, tree)
    sig2 = branch_exclusivity_signature(a2, tree)
    sig3 = branch_exclusivity_signature(a3, tree)

    # a1 and a2 are exclusive at the case level
    assert is_mutually_exclusive_branch_pair(sig1, sig2)
    # a1 and a3 are exclusive at the if/else level
    assert is_mutually_exclusive_branch_pair(sig1, sig3)
    # a2 and a3 are exclusive at the if/else level
    assert is_mutually_exclusive_branch_pair(sig2, sig3)
