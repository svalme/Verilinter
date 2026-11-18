from __future__ import annotations

from pathlib import Path

from src.pkg.parser.elaborated_widths import ElaboratedWidths


def _build(tmp_path: Path, text: str) -> tuple[ElaboratedWidths, Path, str]:
    path = tmp_path / "top.sv"
    path.write_bytes(text.encode("utf-8"))
    return ElaboratedWidths.build([path]), path, text


def _width_of(record: ElaboratedWidths, path: Path, text: str, snippet: str, occurrence: int = 0) -> int | None:
    start = -1
    for _ in range(occurrence + 1):
        start = text.index(snippet, start + 1)
    found = record.widths_at(path, start, start + len(snippet))
    return None if found is None else found.width


STRUCTS = """
module child(input logic i);
endmodule
module top;
  typedef struct packed { logic SR; logic X; } perms_t;
  typedef struct packed { perms_t perms; logic [3:0] a; } cap_t;
  cap_t c;
  child u1(.i(c.perms.SR));
  child u2(.i(c.a[0]));
endmodule
"""


def test_member_of_a_struct_typed_member_has_its_declared_width(tmp_path: Path) -> None:
    record, path, text = _build(tmp_path, STRUCTS)

    assert _width_of(record, path, text, "c.perms.SR") == 1


def test_member_followed_by_a_select_has_its_selected_width(tmp_path: Path) -> None:
    record, path, text = _build(tmp_path, STRUCTS)

    assert _width_of(record, path, text, "c.a[0]") == 1


def test_whole_packed_member_keeps_its_full_width(tmp_path: Path) -> None:
    record, path, text = _build(tmp_path, STRUCTS.replace("c.a[0]", "c.a"))

    assert _width_of(record, path, text.replace("c.a[0]", "c.a"), "c.a") == 4


def test_call_to_a_function_has_its_declared_return_width(tmp_path: Path) -> None:
    record, path, text = _build(
        tmp_path,
        """
        module child(input logic [7:0] i);
        endmodule
        module top;
          function automatic logic [7:0] f(logic [7:0] x); return x; endfunction
          logic [7:0] a;
          child u1(.i(f(a)));
        endmodule
        """,
    )

    assert _width_of(record, path, text, "f(a)") == 8


def test_operand_under_an_implicit_conversion_keeps_its_own_width(tmp_path: Path) -> None:
    record, path, text = _build(
        tmp_path,
        """
        module top;
          logic [7:0] a; logic [3:0] b; wire [7:0] w = a + b;
        endmodule
        """,
    )

    assert _width_of(record, path, text, "b;") is None
    assert _width_of(record, path, text, "b", occurrence=1) == 4


def test_type_parameter_width_is_known_per_instance_and_disagrees_across_instances(tmp_path: Path) -> None:
    record, path, text = _build(
        tmp_path,
        """
        module leaf #(parameter type T = logic [3:0]) (input T d, output logic o);
          assign o = ^d;
        endmodule
        module top(input logic [3:0] a, input logic [7:0] b, output logic x, output logic y);
          leaf #(.T(logic [3:0])) u0(.d(a), .o(x));
          leaf #(.T(logic [7:0])) u1(.d(b), .o(y));
        endmodule
        """,
    )

    start = text.index("^d") + 1
    found = record.widths_at(path, start, start + 1)

    assert found is not None
    assert found.widths == frozenset({4, 8})
    assert found.width is None


def test_unknown_span_has_no_entry(tmp_path: Path) -> None:
    record, path, _text = _build(tmp_path, STRUCTS)

    assert record.widths_at(path, 0, 3) is None


def test_expression_from_a_macro_is_not_recorded(tmp_path: Path) -> None:
    record, path, text = _build(
        tmp_path,
        """
        `define SEL c.a
        module top;
          typedef struct packed { logic [3:0] a; } cap_t;
          cap_t c; logic [3:0] q;
          assign q = `SEL;
        endmodule
        """,
    )

    assert _width_of(record, path, text, "`SEL;") is None


CONNECTIONS = """
module child #(parameter int W = 4) (input logic [W-1:0] a, output logic [1:0] z);
endmodule
module top;
  logic [7:0] q; logic [3:0] p; logic [1:0] r;
  child #(.W(8)) u_wide(.a(q), .z(r));
  child u_default(.a(p), .z());
  for (genvar i = 0; i < 2; i++) begin : g
    child u_arr[1:0](.a(p), .z());
  end
  if (0) begin : g_off
    child u_off(.a(p), .z());
  end
endmodule
"""


def test_connection_widths_use_the_overrides_of_the_instance(tmp_path: Path) -> None:
    record, _path, _text = _build(tmp_path, CONNECTIONS)

    assert record.connection_widths("top", "u_wide", "a") == frozenset({(8, 8)})
    assert record.connection_widths("top", "u_default", "a") == frozenset({(4, 4)})


def test_open_port_has_no_expression_width(tmp_path: Path) -> None:
    record, _path, _text = _build(tmp_path, CONNECTIONS)

    assert record.connection_widths("top", "u_default", "z") == frozenset({(2, None)})


def test_instance_array_in_a_generate_loop_is_found_by_the_array_name(tmp_path: Path) -> None:
    record, _path, _text = _build(tmp_path, CONNECTIONS)

    assert record.connection_widths("top", "u_arr", "a") == frozenset({(4, 4)})


def test_two_instantiations_of_one_parent_with_different_overrides_keep_both_pairs(tmp_path: Path) -> None:
    record, _path, _text = _build(
        tmp_path,
        """
        module child #(parameter int W = 4) (input logic [W-1:0] a);
        endmodule
        module mid #(parameter int N = 4) (input logic [N-1:0] x);
          child #(.W(N)) u_c(.a(x));
        endmodule
        module top(input logic [3:0] p, input logic [7:0] q);
          mid #(.N(4)) u_m4(.x(p));
          mid #(.N(8)) u_m8(.x(q));
        endmodule
        """,
    )

    assert record.connection_widths("mid", "u_c", "a") == frozenset({(4, 4), (8, 8)})


def test_instance_in_a_switched_off_branch_has_no_connection_widths(tmp_path: Path) -> None:
    record, _path, _text = _build(tmp_path, CONNECTIONS)

    assert record.connection_widths("top", "u_off", "a") == frozenset()


def test_unknown_names_give_no_connection_widths(tmp_path: Path) -> None:
    record, _path, _text = _build(tmp_path, CONNECTIONS)

    assert record.connection_widths("top", "u_none", "a") == frozenset()
    assert record.connection_widths(None, "u_wide", "a") == frozenset()


def test_connection_expression_width_is_the_written_expression_not_the_port_type(tmp_path: Path) -> None:
    record, _path, _text = _build(
        tmp_path,
        """
        module child(input logic [7:0] a, output logic [7:0] o);
        endmodule
        module top(input logic [3:0] x, output logic [3:0] y);
          child u_c(.a(x), .o(y));
        endmodule
        """,
    )

    assert record.connection_widths("top", "u_c", "a") == frozenset({(8, 4)})
    assert record.connection_widths("top", "u_c", "o") == frozenset({(8, 4)})

