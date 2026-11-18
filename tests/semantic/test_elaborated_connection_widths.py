from __future__ import annotations

from pathlib import Path

from src.pkg.engine import analyze

PACKAGE = """
package widths_pkg;
  function automatic int wide();
    return 8;
  endfunction
endpackage
"""

CHILD = """
module child (input logic [widths_pkg::wide()-1:0] a);
endmodule
"""


def _codes(tmp_path: Path, top: str, elaborated_widths: bool) -> list[str]:
    paths = []
    for name, text in (("pkg.sv", PACKAGE), ("child.sv", CHILD), ("top.sv", top)):
        path = tmp_path / name
        path.write_bytes(text.encode("utf-8"))
        paths.append(path)
    result = analyze(paths, rule_profile="rtl_strict", elaborated_widths=elaborated_widths)
    return sorted(d["code"] for d in result.diagnostics if d["code"].startswith("PORT_CONNECTION_WIDTH"))


MATCHING = """
module top(input logic [7:0] x);
  child u_c(.a(x));
endmodule
"""

MISMATCHED = """
module top(input logic [3:0] x);
  child u_c(.a(x));
endmodule
"""

PLAIN_MISMATCH = """
module plain (input logic [7:0] a);
endmodule
module top(input logic [3:0] x);
  plain u_p(.a(x));
endmodule
"""


def test_port_width_from_a_package_function_is_unknown_without_the_record(tmp_path: Path) -> None:
    assert _codes(tmp_path, MATCHING, elaborated_widths=False) == ["PORT_CONNECTION_WIDTH_UNKNOWN"]


def test_port_width_from_a_package_function_is_known_with_the_record(tmp_path: Path) -> None:
    assert _codes(tmp_path, MATCHING, elaborated_widths=True) == []


def test_mismatch_through_a_package_function_width_is_reported_with_the_record(tmp_path: Path) -> None:
    assert _codes(tmp_path, MISMATCHED, elaborated_widths=True) == ["PORT_CONNECTION_WIDTH_MISMATCH"]


def test_plain_mismatch_is_reported_with_and_without_the_record(tmp_path: Path) -> None:
    for flag in (False, True):
        assert "PORT_CONNECTION_WIDTH_MISMATCH" in _codes(tmp_path, PLAIN_MISMATCH, elaborated_widths=flag)


LITERALS = """
module plain (input logic [7:0] a, input logic [7:0] b, input logic [7:0] c);
endmodule
module top;
  plain u_p(.a(0), .b('0), .c(4'd0));
endmodule
"""


def test_literal_that_fills_the_port_is_not_a_mismatch_but_a_sized_literal_is(tmp_path: Path) -> None:
    """`0` and `'0` adapt to the port; `4'd0` has its own width, so only it differs from the 8-bit port."""
    result = analyze([_write(tmp_path, "top.sv", LITERALS)], rule_profile="rtl_strict", elaborated_widths=True)
    mismatches = [d for d in result.diagnostics if d["code"] == "PORT_CONNECTION_WIDTH_MISMATCH"]

    assert len(mismatches) == 1
    assert "port 'c'" in mismatches[0]["message"]


def _write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_bytes(text.encode("utf-8"))
    return path

