from __future__ import annotations

from pathlib import Path

from src.run_lint import analyze
from tests.support.scratch import make_scratch

_CHILD = """\
module child(input logic d_i, output logic q_o);
    assign q_o = d_i;
endmodule
"""


def _codes(parent: str) -> list[str]:
    root = make_scratch("_tmp_instance_driver_scopes", "case")
    (root / "child.sv").write_text(_CHILD, encoding="utf-8")
    (root / "parent.sv").write_text(parent, encoding="utf-8")
    paths: list[Path] = [root / "child.sv", root / "parent.sv"]
    return [d["code"] for d in analyze(paths).diagnostics if str(d.get("file", "")).endswith("parent.sv")]


class TestInstanceDriversInGenerateScopes:
    def test_same_named_wires_in_two_generate_blocks_are_not_one_net(self) -> None:
        codes = _codes("""\
module parent(input logic a_i, output logic y_o, output logic z_o);
    if (1) begin : first
        wire w;
        child u (.d_i(a_i), .q_o(w));
        assign y_o = w;
    end
    if (1) begin : second
        wire w;
        child u (.d_i(a_i), .q_o(w));
        assign z_o = w;
    end
endmodule
""")
        assert "MULTIPLE_INSTANCE_DRIVER_CONFLICT" not in codes

    def test_two_instances_on_one_wire_in_a_generate_block_conflict(self) -> None:
        codes = _codes("""\
module parent(input logic a_i, output logic y_o);
    if (1) begin : blk
        wire w;
        child u1 (.d_i(a_i), .q_o(w));
        child u2 (.d_i(a_i), .q_o(w));
        assign y_o = w;
    end
endmodule
""")
        assert codes.count("MULTIPLE_INSTANCE_DRIVER_CONFLICT") == 1

    def test_instance_output_and_an_assign_on_one_generate_wire_conflict(self) -> None:
        codes = _codes("""\
module parent(input logic a_i, output logic y_o);
    if (1) begin : blk
        wire w;
        child u (.d_i(a_i), .q_o(w));
        assign w = a_i;
        assign y_o = w;
    end
endmodule
""")
        assert codes.count("INSTANCE_OUTPUT_DRIVER_CONFLICT") == 1

    def test_generate_wire_on_an_instance_output_is_driven(self) -> None:
        codes = _codes("""\
module parent(input logic a_i, output logic y_o);
    if (1) begin : blk
        wire w;
        child u (.d_i(a_i), .q_o(w));
        assign y_o = w;
    end
endmodule
""")
        assert "NO_UNDRIVEN_SIGNAL" not in codes

    def test_generate_wire_on_an_instance_input_only_is_undriven(self) -> None:
        codes = _codes("""\
module parent(output logic y_o, output logic z_o);
    if (1) begin : blk
        logic s;
        wire w;
        child u (.d_i(s), .q_o(w));
        assign y_o = w;
        assign z_o = s;
    end
endmodule
""")
        assert codes.count("NO_UNDRIVEN_SIGNAL") == 1
