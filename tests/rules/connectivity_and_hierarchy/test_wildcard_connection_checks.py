from __future__ import annotations

from pathlib import Path

from src.run_lint import analyze
from tests.support.scratch import make_scratch

_CHILD = """\
module child(input logic [7:0] d_i, input logic en_i, output logic [7:0] q_o);
    assign q_o = en_i ? d_i : '0;
endmodule
"""


def _codes(parent: str) -> list[str]:
    root = make_scratch("_tmp_wildcard_checks", "case")
    (root / "child.sv").write_text(_CHILD, encoding="utf-8")
    (root / "parent.sv").write_text(parent, encoding="utf-8")
    paths: list[Path] = [root / "child.sv", root / "parent.sv"]
    return [d["code"] for d in analyze(paths).diagnostics if str(d.get("file", "")).endswith("parent.sv")]


class TestWildcardConnectionChecks:
    def test_wildcard_compares_the_port_with_the_signal_of_the_same_name(self) -> None:
        codes = _codes("""\
module parent(input logic [3:0] d_i, input logic en_i, output logic [7:0] q_o);
    child u (.*);
endmodule
""")
        assert codes.count("PORT_CONNECTION_WIDTH_MISMATCH") == 1

    def test_matching_widths_through_a_wildcard_are_clean(self) -> None:
        codes = _codes("""\
module parent(input logic [7:0] d_i, input logic en_i, output logic [7:0] q_o);
    child u (.*);
endmodule
""")
        assert "PORT_CONNECTION_WIDTH_MISMATCH" not in codes
        assert "NO_UNCONNECTED_INSTANCE_PORTS" not in codes

    def test_explicit_connection_beside_a_wildcard_is_checked(self) -> None:
        codes = _codes("""\
module parent(input logic [3:0] a_i, input logic en_i, output logic [7:0] q_o);
    child u (.d_i(a_i), .*);
endmodule
""")
        assert codes.count("PORT_CONNECTION_WIDTH_MISMATCH") == 1

    def test_unnamed_port_left_open_beside_a_wildcard_is_not_reported(self) -> None:
        codes = _codes("""\
module parent(input logic [7:0] d_i, output logic [7:0] q_o);
    child u (.*);
endmodule
""")
        assert "NO_UNCONNECTED_INSTANCE_PORTS" not in codes

    def test_empty_parentheses_beside_a_wildcard_are_reported(self) -> None:
        codes = _codes("""\
module parent(input logic [7:0] d_i, input logic en_i, output logic [7:0] q_o);
    child u (.q_o(), .*);
endmodule
""")
        assert codes.count("NO_UNCONNECTED_INSTANCE_PORTS") == 1
