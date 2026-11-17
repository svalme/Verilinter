from __future__ import annotations

from pathlib import Path

from src.pkg.handlers.register_handlers import *  # noqa: F401,F403
from src.pkg.parser.elaborated_widths import ElaboratedWidths
from src.pkg.parser.parse import parse_file
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.semantic.width_resolver import ResolvedWidth, WidthResolver, WidthSource
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker


def _resolve(tmp_path: Path, text: str, snippet: str, with_record: bool = True, kind: str | None = None) -> ResolvedWidth:
    """Resolve the width of the syntax node whose text is `snippet`, walking the file as the linter does."""
    path = tmp_path / "top.sv"
    path.write_bytes(text.encode("utf-8"))
    tree = parse_file(path)
    record = ElaboratedWidths.build([path]) if with_record else None
    found: list[tuple[object, object]] = []

    def on_node(vnode: object, ctx: object) -> None:
        raw = getattr(vnode, "raw", None)
        if raw is not None and str(raw).strip() == snippet and (kind is None or raw.kind.name == kind):
            found.append((raw, ctx.scope()))

    table = SymbolTable()
    table.set_current_file(str(path))
    Walker(dispatch).walk(tree.root, tree, Context(scope=table.global_scope), table, on_node=on_node)
    assert found, f"no node with text {snippet!r}"
    raw, scope = found[0]
    return WidthResolver(record).resolve(scope, raw, tree)


STRUCT_MEMBER = """
module child(input logic i);
endmodule
module top;
  typedef struct packed { logic SR; logic X; } perms_t;
  typedef struct packed { perms_t perms; logic [3:0] a; } cap_t;
  cap_t c;
  child u1(.i(c.perms.SR));
endmodule
"""

TYPE_PARAMETER = """
module leaf #(parameter type T = logic [3:0]) (input T d, output logic o);
  assign o = ^d;
endmodule
module top(input logic [3:0] a, input logic [7:0] b, output logic x, output logic y);
  leaf #(.T(logic [3:0])) u0(.d(a), .o(x));
  leaf #(.T(logic [7:0])) u1(.d(b), .o(y));
endmodule
"""

SWITCHED_OFF = """
module off_leaf(input logic [7:0] a, output logic y);
  assign y = ^a;
endmodule
module top(input logic [7:0] x, output logic z);
  if (0) begin : gen_off
    off_leaf u_off(.a(x), .y(z));
  end
endmodule
"""


def test_width_slang_computes_for_one_instance_is_elaborated(tmp_path: Path) -> None:
    resolved = _resolve(tmp_path, STRUCT_MEMBER, "c.perms.SR")

    assert resolved.source == WidthSource.ELABORATED
    assert resolved.width == 1
    assert resolved.estimator_width is None  # the estimator cannot size a member of a struct-typed member


def test_instances_with_different_widths_give_the_set_and_no_single_width(tmp_path: Path) -> None:
    resolved = _resolve(tmp_path, TYPE_PARAMETER, "d", kind="IdentifierName")

    assert resolved.source == WidthSource.INSTANCES_DISAGREE
    assert resolved.width is None
    assert resolved.elaborated_widths == frozenset({4, 8})


def test_code_slang_does_not_elaborate_falls_back_to_the_estimator(tmp_path: Path) -> None:
    resolved = _resolve(tmp_path, SWITCHED_OFF, "a", kind="IdentifierName")

    assert resolved.source == WidthSource.ESTIMATOR_DEFAULTS
    assert resolved.width == 8
    assert resolved.elaborated_widths == frozenset()


def test_width_neither_source_knows_is_unknown(tmp_path: Path) -> None:
    resolved = _resolve(tmp_path, SWITCHED_OFF.replace("^a", "^f(a)"), "f(a)")

    assert resolved.source == WidthSource.UNKNOWN
    assert resolved.width is None


def test_without_a_record_the_estimator_answers(tmp_path: Path) -> None:
    resolved = _resolve(tmp_path, SWITCHED_OFF, "a", with_record=False, kind="IdentifierName")

    assert resolved.source == WidthSource.ESTIMATOR_DEFAULTS
    assert resolved.width == 8


def test_expression_from_a_macro_uses_the_estimator(tmp_path: Path) -> None:
    resolved = _resolve(
        tmp_path,
        """
        `define PICK a
        module top(input logic [7:0] a, output logic [7:0] q);
          assign q = `PICK;
        endmodule
        """,
        "a",
        kind="IdentifierName",
    )

    assert resolved.source == WidthSource.ESTIMATOR_DEFAULTS
    assert resolved.elaborated_widths == frozenset()
