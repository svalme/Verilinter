from __future__ import annotations

from pathlib import Path

from src.run_lint import analyze
from tests.support.scratch import make_scratch

_CHILD = """\
module child(input logic d_i, output logic q_o);
    assign q_o = d_i;
endmodule
"""


def _undriven(parent: str, child: str | None = _CHILD) -> list[str]:
    """Names reported by NO_UNDRIVEN_SIGNAL for `parent`, with the child module in its own file."""
    root = make_scratch("_tmp_instance_driven", "case")
    paths: list[Path] = []
    if child is not None:
        (root / "child.sv").write_text(child, encoding="utf-8")
        paths.append(root / "child.sv")
    (root / "parent.sv").write_text(parent, encoding="utf-8")
    paths.append(root / "parent.sv")
    result = analyze(paths)
    return [
        d["message"].split("'")[1]
        for d in result.diagnostics
        if d["code"] == "NO_UNDRIVEN_SIGNAL" and str(d.get("file", "")).endswith("parent.sv")
    ]


class TestInstanceDrivenSignals:
    def test_signal_on_a_child_output_in_another_file_counts_as_driven(self) -> None:
        parent = """\
module parent(input logic a_i, output logic y_o);
    logic w;
    child u (.d_i(a_i), .q_o(w));
    assign y_o = w;
endmodule
"""
        assert _undriven(parent) == []

    def test_signal_wired_only_to_a_child_input_is_undriven(self) -> None:
        parent = """\
module parent(output logic y_o, output logic z_o);
    logic s;
    logic w;
    child u (.d_i(s), .q_o(w));
    assign y_o = w;
    assign z_o = s;
endmodule
"""
        assert _undriven(parent) == ["s"]

    def test_wildcard_connection_to_a_child_output_counts_as_driven(self) -> None:
        parent = """\
module parent(input logic d_i, output logic y_o);
    logic q_o;
    child u (.*);
    assign y_o = q_o;
endmodule
"""
        assert _undriven(parent) == []

    def test_ordered_connection_uses_the_port_order(self) -> None:
        parent = """\
module parent(input logic a_i, output logic y_o);
    logic w;
    child u (a_i, w);
    assign y_o = w;
endmodule
"""
        assert _undriven(parent) == []

    def test_child_declared_in_no_file_leaves_the_signal_alone(self) -> None:
        parent = """\
module parent(output logic y_o);
    logic w;
    unknown_child u (.q_o(w));
    assign y_o = w;
endmodule
"""
        assert _undriven(parent, child=None) == []

    def test_child_in_the_same_file_counts_the_same_way(self) -> None:
        parent = _CHILD + """\
module parent(output logic y_o, output logic z_o);
    logic s;
    logic w;
    child u (.d_i(s), .q_o(w));
    assign y_o = w;
    assign z_o = s;
endmodule
"""
        assert _undriven(parent, child=None) == ["s"]
