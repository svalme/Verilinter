from __future__ import annotations

from pathlib import Path

from src.run_lint import analyze
from tests.support.scratch import make_scratch

_CHILD = """\
module child(input logic d_i, output logic q_o);
    assign q_o = d_i;
endmodule

module wide(input logic d_i, output logic [1:0] q_o);
    assign q_o = {d_i, d_i};
endmodule
"""


def _codes(parent: str) -> list[str]:
    root = make_scratch("_tmp_instance_driven_selects", "case")
    (root / "child.sv").write_text(_CHILD, encoding="utf-8")
    (root / "parent.sv").write_text(parent, encoding="utf-8")
    paths: list[Path] = [root / "child.sv", root / "parent.sv"]
    return [d["code"] for d in analyze(paths).diagnostics if str(d.get("file", "")).endswith("parent.sv")]


class TestSelectConnections:
    def test_two_instances_on_different_bits_of_one_bus_do_not_conflict(self) -> None:
        codes = _codes("""\
module parent(input logic a_i, output logic [1:0] y_o);
    wire [1:0] w;
    child u0 (.d_i(a_i), .q_o(w[0]));
    child u1 (.d_i(a_i), .q_o(w[1]));
    assign y_o = w;
endmodule
""")
        assert "MULTIPLE_INSTANCE_DRIVER_CONFLICT" not in codes

    def test_two_instances_on_the_same_bit_conflict(self) -> None:
        codes = _codes("""\
module parent(input logic a_i, output logic y_o);
    wire [1:0] w;
    child u0 (.d_i(a_i), .q_o(w[0]));
    child u1 (.d_i(a_i), .q_o(w[0]));
    assign y_o = w[0];
endmodule
""")
        assert codes.count("MULTIPLE_INSTANCE_DRIVER_CONFLICT") == 1

    def test_instance_bit_and_assign_to_another_bit_do_not_conflict(self) -> None:
        codes = _codes("""\
module parent(input logic a_i, output logic [1:0] y_o);
    wire [1:0] w;
    child u0 (.d_i(a_i), .q_o(w[0]));
    assign w[1] = a_i;
    assign y_o = w;
endmodule
""")
        assert "INSTANCE_OUTPUT_DRIVER_CONFLICT" not in codes

    def test_instance_bit_and_assign_to_the_same_bit_conflict(self) -> None:
        codes = _codes("""\
module parent(input logic a_i, output logic [1:0] y_o);
    wire [1:0] w;
    child u0 (.d_i(a_i), .q_o(w[0]));
    assign w[0] = a_i;
    assign y_o = w;
endmodule
""")
        assert codes.count("INSTANCE_OUTPUT_DRIVER_CONFLICT") == 1

    def test_a_bus_driven_only_through_selects_is_driven(self) -> None:
        codes = _codes("""\
module parent(input logic a_i, output logic [1:0] y_o);
    wire [1:0] w;
    child u0 (.d_i(a_i), .q_o(w[0]));
    child u1 (.d_i(a_i), .q_o(w[1]));
    assign y_o = w;
endmodule
""")
        assert "NO_UNDRIVEN_SIGNAL" not in codes

    def test_a_bus_read_only_through_an_input_select_is_undriven(self) -> None:
        codes = _codes("""\
module parent(output logic y_o);
    logic [1:0] s;
    wire w;
    child u0 (.d_i(s[0]), .q_o(w));
    assign y_o = w;
endmodule
""")
        assert codes.count("NO_UNDRIVEN_SIGNAL") == 1

    def test_one_instance_per_bit_in_a_generate_loop_does_not_conflict(self) -> None:
        codes = _codes("""\
module parent(input logic a_i, output logic [3:0] y_o);
    wire [3:0] w;
    for (genvar i = 0; i < 4; i++) begin : g
        child u (.d_i(a_i), .q_o(w[i]));
    end
    assign y_o = w;
endmodule
""")
        assert "MULTIPLE_INSTANCE_DRIVER_CONFLICT" not in codes
        assert "INSTANCE_OUTPUT_DRIVER_CONFLICT" not in codes
        assert "NO_UNDRIVEN_SIGNAL" not in codes

    def test_loop_body_parameter_from_the_genvar_selects_distinct_bits(self) -> None:
        codes = _codes("""module parent(input logic a_i, output logic [3:0] y_o);
    localparam int BASE = 1;
    wire [3:0] w;
    child u0 (.d_i(a_i), .q_o(w[0]));
    for (genvar i = 0; i < 3; i++) begin : g
        localparam int Cnt = i + BASE;
        assign w[Cnt] = a_i;
    end
    assign y_o = w;
endmodule
""")
        assert "INSTANCE_OUTPUT_DRIVER_CONFLICT" not in codes
        assert "NO_MULTIPLE_DRIVERS" not in codes

    def test_loop_body_parameter_reaching_the_instance_bit_conflicts(self) -> None:
        codes = _codes("""module parent(input logic a_i, output logic [3:0] y_o);
    localparam int BASE = 0;
    wire [3:0] w;
    child u0 (.d_i(a_i), .q_o(w[0]));
    for (genvar i = 0; i < 3; i++) begin : g
        localparam int Cnt = i + BASE;
        assign w[Cnt] = a_i;
    end
    assign y_o = w;
endmodule
""")
        assert codes.count("INSTANCE_OUTPUT_DRIVER_CONFLICT") == 1


class TestConcatenationConnections:
    def test_each_member_of_an_output_concatenation_is_driven(self) -> None:
        codes = _codes("""\
module parent(input logic a_i, output logic y_o, output logic z_o);
    wire p, q;
    wide u (.d_i(a_i), .q_o({p, q}));
    assign y_o = p;
    assign z_o = q;
endmodule
""")
        assert "NO_UNDRIVEN_SIGNAL" not in codes

    def test_a_member_of_an_output_concatenation_that_is_also_assigned_conflicts(self) -> None:
        codes = _codes("""\
module parent(input logic a_i, output logic y_o, output logic z_o);
    wire p, q;
    wide u (.d_i(a_i), .q_o({p, q}));
    assign p = a_i;
    assign y_o = p;
    assign z_o = q;
endmodule
""")
        assert codes.count("INSTANCE_OUTPUT_DRIVER_CONFLICT") == 1

    def test_an_input_expression_that_is_not_a_reference_names_no_signal(self) -> None:
        codes = _codes("""\
module parent(input logic a_i, input logic b_i, output logic y_o);
    wire w;
    child u (.d_i(a_i & b_i), .q_o(w));
    assign y_o = w;
endmodule
""")
        assert "NO_UNDRIVEN_SIGNAL" not in codes
