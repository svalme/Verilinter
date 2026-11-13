from __future__ import annotations

from src.run_lint import analyze
from tests.support.scratch import make_scratch

_CHILD = """\
module child(input logic d_i, output logic q_o);
    assign q_o = d_i;
endmodule
"""


def _messages(source: str, code: str = "NO_UNDRIVEN_SIGNAL") -> list[str]:
    root = make_scratch("_tmp_partial_drive", "case")
    (root / "child.sv").write_text(_CHILD, encoding="utf-8")
    (root / "top.sv").write_text(source, encoding="utf-8")
    result = analyze([root / "child.sv", root / "top.sv"])
    return [d["message"] for d in result.diagnostics if d["code"] == code and str(d.get("file", "")).endswith("top.sv")]


class TestPartlyDrivenVectors:
    def test_a_bit_no_write_reaches_is_reported(self) -> None:
        messages = _messages("""\
module top(input logic a_i, input logic b_i, output logic [3:0] y_o);
    wire [3:0] x;
    assign x[0] = a_i;
    assign x[3:2] = {b_i, a_i};
    assign y_o = x;
endmodule
""")
        assert messages == ["Signal 'x' is driven only in part: bits [1] are never driven"]

    def test_several_runs_are_listed_highest_first(self) -> None:
        messages = _messages("""\
module top(input logic a_i, output logic y_o);
    wire [15:10] x;
    assign x[15] = a_i;
    assign x[12] = a_i;
    assign x[10] = a_i;
    assign y_o = |x;
endmodule
""")
        assert messages == ["Signal 'x' is driven only in part: bits [14:13], [11] are never driven"]

    def test_writes_that_cover_every_bit_are_not_reported(self) -> None:
        messages = _messages("""\
module top(input logic a_i, output logic [3:0] y_o);
    wire [3:0] x;
    assign x[1:0] = {a_i, a_i};
    assign x[3] = a_i;
    assign x[2] = a_i;
    assign y_o = x;
endmodule
""")
        assert messages == []

    def test_a_write_to_the_whole_vector_covers_it(self) -> None:
        messages = _messages("""\
module top(input logic a_i, output logic [3:0] y_o);
    wire [3:0] x;
    assign x = {4{a_i}};
    assign y_o = x;
endmodule
""")
        assert messages == []

    def test_a_write_with_a_variable_index_is_not_guessed_at(self) -> None:
        messages = _messages("""\
module top(input logic a_i, input logic [1:0] i_i, output logic [3:0] y_o);
    logic [3:0] x;
    always_comb begin
        x = '0;
        x[i_i] = a_i;
    end
    assign y_o = x;
endmodule
""")
        assert messages == []

    def test_a_vector_that_is_never_read_is_not_reported(self) -> None:
        messages = _messages("""\
module top(input logic a_i, output logic y_o);
    wire [3:0] x;
    assign x[0] = a_i;
    assign y_o = a_i;
endmodule
""")
        assert messages == []

    def test_a_vector_with_nothing_written_keeps_the_whole_signal_message(self) -> None:
        messages = _messages("""\
module top(output logic y_o);
    wire [3:0] x;
    assign y_o = x[0];
endmodule
""")
        assert messages == ["Signal 'x' is read but never driven"]

    def test_instance_outputs_on_some_bits_leave_the_others_reported(self) -> None:
        messages = _messages("""\
module top(input logic a_i, output logic [2:0] y_o);
    wire [2:0] w;
    child u0 (.d_i(a_i), .q_o(w[0]));
    child u2 (.d_i(a_i), .q_o(w[2]));
    assign y_o = w;
endmodule
""")
        assert messages == ["Signal 'w' is driven only in part: bits [1] are never driven"]

    def test_a_generate_loop_that_drives_every_bit_covers_the_vector(self) -> None:
        messages = _messages("""\
module top(input logic a_i, output logic [3:0] y_o);
    wire [3:0] w;
    for (genvar i = 0; i < 4; i++) begin : g
        child u (.d_i(a_i), .q_o(w[i]));
    end
    assign y_o = w;
endmodule
""")
        assert messages == []

    def test_a_generate_loop_that_stops_short_leaves_the_rest_reported(self) -> None:
        messages = _messages("""\
module top(input logic a_i, output logic [3:0] y_o);
    wire [3:0] w;
    for (genvar i = 0; i < 3; i++) begin : g
        child u (.d_i(a_i), .q_o(w[i]));
    end
    assign y_o = w;
endmodule
""")
        assert messages == ["Signal 'w' is driven only in part: bits [3] are never driven"]

    def test_an_unpacked_array_is_left_alone(self) -> None:
        messages = _messages("""\
module top(input logic a_i, output logic y_o);
    logic [3:0] m [2];
    assign m[0] = {4{a_i}};
    assign y_o = m[0][0];
endmodule
""")
        assert messages == []

    def test_a_connection_with_an_unknown_child_is_left_alone(self) -> None:
        messages = _messages("""\
module top(input logic a_i, output logic [3:0] y_o);
    wire [3:0] w;
    assign w[0] = a_i;
    unknown_child u (.q_o(w[3:1]));
    assign y_o = w;
endmodule
""")
        assert messages == []
