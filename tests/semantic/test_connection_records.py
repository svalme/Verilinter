from __future__ import annotations

from pathlib import Path

from src.run_lint import analyze
from tests.support.scratch import make_scratch

_CHILD = """\
module child #(parameter W = 4)(input logic [W-1:0] d_i, input logic en_i, output logic [W-1:0] q_o);
    assign q_o = en_i ? d_i : '0;
endmodule
"""


def _records(parent: str, child: str | None = _CHILD, instance: int = 0):
    """The connection records of one instance of `parent`, with the child module in its own file."""
    root = make_scratch("_tmp_connection_records", "case")
    paths: list[Path] = []
    if child is not None:
        (root / "child.sv").write_text(child, encoding="utf-8")
        paths.append(root / "child.sv")
    (root / "parent.sv").write_text(parent, encoding="utf-8")
    paths.append(root / "parent.sv")
    result = analyze(paths)
    instances = [inst for inst in result.symbol_table.instantiations if inst.parent_module == "parent"]
    return instances[instance].connection_records


def _by_port(records):
    return {record.port_name: record for record in records}


class TestConnectionRecords:
    def test_named_connections_pair_each_port_with_its_signal(self) -> None:
        records = _by_port(_records("""\
module parent(input logic [3:0] a_i, input logic e_i, output logic [3:0] y_o);
    logic [3:0] w;
    child u (.d_i(a_i), .en_i(e_i), .q_o(w));
    assign y_o = w;
endmodule
"""))
        assert set(records) == {"d_i", "en_i", "q_o"}
        assert records["q_o"].direction == "output"
        assert records["q_o"].signal is not None and records["q_o"].signal.name == "w"
        assert records["d_i"].direction == "input"
        assert records["d_i"].port_width == 4 and records["d_i"].expr_width == 4

    def test_ordered_connections_follow_the_port_order(self) -> None:
        records = _records("""\
module parent(input logic [3:0] a_i, input logic e_i, output logic [3:0] y_o);
    child u (a_i, e_i, y_o);
endmodule
""")
        assert [(r.port_name, r.signal.name if r.signal else None) for r in records] == [
            ("d_i", "a_i"),
            ("en_i", "e_i"),
            ("q_o", "y_o"),
        ]

    def test_a_port_left_off_the_list_has_no_connection(self) -> None:
        records = _by_port(_records("""\
module parent(input logic [3:0] a_i, output logic [3:0] y_o);
    child u (.d_i(a_i), .q_o(y_o));
endmodule
"""))
        assert records["en_i"].connection is None
        assert records["en_i"].implicit is False

    def test_wildcard_connects_unlisted_ports_by_name(self) -> None:
        records = _by_port(_records("""\
module parent(input logic [3:0] d_i, input logic en_i, output logic [3:0] q_o);
    child u (.*);
endmodule
"""))
        assert records["d_i"].implicit is True
        assert records["d_i"].signal is not None and records["d_i"].signal.name == "d_i"
        assert records["d_i"].expr_width == 4

    def test_port_width_follows_the_parameter_override(self) -> None:
        records = _by_port(_records("""\
module parent(input logic [7:0] a_i, input logic e_i, output logic [7:0] y_o);
    child #(.W(8)) u (.d_i(a_i), .en_i(e_i), .q_o(y_o));
endmodule
"""))
        assert records["d_i"].port_width == 8

    def test_shorthand_in_a_generate_block_finds_its_signal(self) -> None:
        records = _by_port(_records("""\
module parent #(parameter N = 1)(input logic [3:0] d_i, input logic en_i, output logic [3:0] q_o);
    if (N == 1) begin : g
        child u (.d_i, .en_i, .q_o);
    end
endmodule
"""))
        assert records["q_o"].signal is not None and records["q_o"].signal.name == "q_o"

    def test_unknown_child_gives_records_without_ports(self) -> None:
        records = _records("""\
module parent(input logic a_i, output logic y_o);
    missing u (.x_i(a_i), .z_o(y_o));
endmodule
""", child=None)
        assert [(r.port_name, r.port, r.direction) for r in records] == [("x_i", None, None), ("z_o", None, None)]
        assert records[0].signal is not None

    def test_a_named_connection_to_a_missing_port_has_no_port(self) -> None:
        records = _by_port(_records("""\
module parent(input logic [3:0] a_i, output logic [3:0] y_o);
    child u (.d_i(a_i), .bogus_i(a_i), .q_o(y_o));
endmodule
"""))
        assert records["bogus_i"].port is None
        assert records["bogus_i"].connection is not None
