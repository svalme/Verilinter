import pytest

from src.pkg.handlers.register_handlers import *
from src.pkg.parser.parse import parse_text
from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.walk.walker import Walker
from tests.support.lint_harness import run_inline_lint_case
from tests.support.parse_diagnostics import assert_no_parse_errors


def _walk(code: str) -> SymbolTable:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    tree = parse_text(code)
    assert_no_parse_errors("tests/semantic/test_interface_member_tracking.py", tree)
    Walker(dispatch).walk(tree.root, tree, ctx, symbol_table)
    return symbol_table


def _member(symbol_table: SymbolTable, interface: str, name: str) -> Symbol:
    scope = symbol_table.lookup_module(interface)
    assert scope is not None
    symbol = scope.lookup(name)
    assert symbol is not None
    return symbol


IFACE = """
interface bus_if;
  logic req;
  logic gnt;
  logic idle;
  modport mp(input req, output gnt);
endinterface
"""


class TestInterfaceMemberTracking:
    def test_member_read_and_write_through_ansi_interface_port(self) -> None:
        table = _walk(IFACE + "module sub(bus_if b); assign b.gnt = b.req; endmodule")
        assert _member(table, "bus_if", "req").is_read
        assert not _member(table, "bus_if", "req").is_written
        assert _member(table, "bus_if", "gnt").is_written
        assert not _member(table, "bus_if", "gnt").is_read
        assert not _member(table, "bus_if", "idle").is_read

    def test_interface_declared_after_its_use(self) -> None:
        table = _walk("module sub(bus_if b); assign b.gnt = b.req; endmodule" + IFACE)
        assert _member(table, "bus_if", "req").is_read
        assert _member(table, "bus_if", "gnt").is_written

    def test_modport_qualified_port(self) -> None:
        table = _walk(IFACE + "module sub(bus_if.mp b); assign b.gnt = b.req; endmodule")
        assert _member(table, "bus_if", "req").is_read
        assert _member(table, "bus_if", "gnt").is_written

    def test_non_ansi_interface_port(self) -> None:
        table = _walk(IFACE + "module sub(b); bus_if.mp b; assign b.gnt = b.req; endmodule")
        assert _member(table, "bus_if", "req").is_read
        assert _member(table, "bus_if", "gnt").is_written

    def test_member_reached_through_interface_instance(self) -> None:
        table = _walk(IFACE + "module top(output logic o); bus_if bus(); assign o = bus.req; endmodule")
        assert _member(table, "bus_if", "req").is_read

    def test_uses_of_one_member_accumulate_across_modules(self) -> None:
        code = IFACE + """
module a(bus_if b); assign b.gnt = 1'b1; endmodule
module c(bus_if b); logic x; assign x = b.gnt; endmodule
"""
        gnt = _member(_walk(code), "bus_if", "gnt")
        assert gnt.is_read and gnt.is_written

    def test_member_selector_on_undeclared_interface_is_ignored(self) -> None:
        table = _walk("module sub(missing_if b); logic x; assign x = b.req; endmodule")
        assert table.pending_hierarchical_uses == []

    def test_struct_member_access_does_not_touch_interface_members(self) -> None:
        code = IFACE + """
module sub;
  typedef struct packed { logic req; } s_t;
  s_t s;
  logic x;
  assign x = s.req;
endmodule
"""
        assert not _member(_walk(code), "bus_if", "req").is_read


class TestInterfaceMemberDiagnostics:
    def test_member_used_through_port_is_not_unused(self) -> None:
        result = run_inline_lint_case(
            {"bus_if.sv": IFACE + "module sub(bus_if b); assign b.gnt = b.req; endmodule"}
        )
        unused_names = [d["message"] for d in result.diagnostics if d["code"] == "UNUSED_VARIABLE"]
        assert all("'req'" not in m and "'gnt'" not in m for m in unused_names)
        assert any("'idle'" in m for m in unused_names)

    def test_read_member_that_nothing_drives_is_undriven(self) -> None:
        result = run_inline_lint_case(
            {"bus_if.sv": IFACE + "module sub(bus_if b); logic x; assign x = b.req; endmodule"}
        )
        assert any(d["code"] == "NO_UNDRIVEN_SIGNAL" and "'req'" in d["message"] for d in result.diagnostics)

    def test_driven_member_that_nothing_reads_is_write_only(self) -> None:
        result = run_inline_lint_case(
            {"bus_if.sv": IFACE + "module sub(bus_if b); assign b.gnt = 1'b1; endmodule"}
        )
        assert any(d["code"] == "NO_WRITE_ONLY_VARIABLE" and "'gnt'" in d["message"] for d in result.diagnostics)
