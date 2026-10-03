from pathlib import Path

import pytest

from src.pkg.parser.parse import parse_file
from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.semantic.symbol import Symbol
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.declarations_and_types.no_implicit_net import NoImplicitNetRule

from tests.support.lint_harness import run_inline_lint_case

DATA = Path(__file__).parent.parent.parent / "data"


class TestNoImplicitNetRule:
    @pytest.fixture
    def rule(self) -> NoImplicitNetRule:
        return NoImplicitNetRule()

    def test_rule_has_correct_code(self, rule: NoImplicitNetRule) -> None:
        assert rule.code == "NO_IMPLICIT_NET"

    def test_flags_implicit_net_symbol(self, rule: NoImplicitNetRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="a", kind="implicit_net")
        sym.is_implicit = True
        sym.add_use({"line": 4, "col": 5}, read=True)
        st.global_scope.define(sym)

        diagnostics = rule.run(st)

        assert len(diagnostics) == 1
        assert diagnostics[0]["line"] == 4
        assert diagnostics[0]["col"] == 5
        assert "a" in diagnostics[0]["message"]

    def test_does_not_flag_declared_symbol(self, rule: NoImplicitNetRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="a", kind="variable")
        sym.add_declaration({"line": 2, "col": 8})
        sym.add_use({"line": 4, "col": 5}, read=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_does_not_flag_non_implicit_undeclared_symbol(self, rule: NoImplicitNetRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="a", kind="variable")
        sym.add_use({"line": 4, "col": 5}, read=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_against_real_parsed_file(self, rule: NoImplicitNetRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        path = DATA / "simple.v"
        symbol_table.set_current_file(str(path))
        tree = parse_file(path)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        flagged_names = {d["message"].split("'")[1] for d in diagnostics}
        assert flagged_names == {"a", "b", "c", "d", "out", "y", "z", "sel"}

    def test_does_not_flag_when_file_uses_default_nettype_none(self, rule: NoImplicitNetRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        path = DATA / "default_nettype_none.v"
        symbol_table.set_current_file(str(path))
        symbol_table.set_current_file_default_nettype_none(True)
        tree = parse_file(path)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []


class TestNoImplicitNetPackageScoping:
    """A package/`import` declared in the same file must not manufacture false
    implicit nets."""

    def test_wildcard_import_bare_name_is_not_implicit(self) -> None:
        result = run_inline_lint_case(
            {
                "top.sv": """
                package my_pkg;
                  parameter int FOO = 1;
                endpackage
                module top;
                  import my_pkg::*;
                  logic [7:0] x;
                  assign x = FOO;
                endmodule
                """
            }
        )
        result.expect_no_code("NO_IMPLICIT_NET")

    def test_explicit_import_of_specific_name_is_not_implicit(self) -> None:
        result = run_inline_lint_case(
            {
                "top.sv": """
                package my_pkg;
                  parameter int FOO = 1;
                endpackage
                module top;
                  import my_pkg::FOO;
                  logic [7:0] x;
                  assign x = FOO;
                endmodule
                """
            }
        )
        result.expect_no_code("NO_IMPLICIT_NET")

    def test_scoped_name_reference_is_not_implicit(self) -> None:
        result = run_inline_lint_case(
            {
                "top.sv": """
                package my_pkg;
                  parameter int FOO = 1;
                endpackage
                module top;
                  logic [7:0] x;
                  assign x = my_pkg::FOO;
                endmodule
                """
            }
        )
        result.expect_no_code("NO_IMPLICIT_NET")

    def test_package_internal_cross_reference_is_not_implicit(self) -> None:
        """A package's own declarations referencing each other (both in the same
        flat package scope) must resolve via ordinary same-scope lookup."""
        result = run_inline_lint_case(
            {
                "top.sv": """
                package my_pkg;
                  parameter int FOO = 1;
                  parameter int BAR = FOO + 1;
                endpackage
                module top;
                  logic [7:0] x;
                  assign x = my_pkg::BAR;
                endmodule
                """
            }
        )
        result.expect_no_code("NO_IMPLICIT_NET")

    def test_scoped_name_to_package_not_declared_in_file_is_conservatively_skipped(self) -> None:
        """Cross-file package resolution isn't supported, so a reference to a
        package this file never declares must be skipped rather than flagged as an implicit net."""
        result = run_inline_lint_case(
            {
                "top.sv": """
                module top;
                  logic [7:0] x;
                  assign x = other_pkg::FOO;
                endmodule
                """
            }
        )
        result.expect_no_code("NO_IMPLICIT_NET")

    def test_struct_field_member_access_is_not_treated_as_package_scope(self) -> None:
        """pyslang represents BOTH `pkg::name` and `struct_var.field` with the
        same `ScopedNameSyntax` node, distinguished only by the separator
        token (`::` vs `.`). A struct-typed variable's own field access must
        not be misread as a package-qualified reference (e.g. `perms.U0` on a
        `perms_t` struct)."""
        result = run_inline_lint_case(
            {
                "top.sv": """
                package my_pkg;
                  typedef struct packed { logic u0; logic se; } perms_t;
                endpackage
                module top;
                  import my_pkg::*;
                  perms_t perms;
                  logic x;
                  always @* begin
                    perms.u0 = 1'b1;
                    x = perms.u0;
                  end
                endmodule
                """
            }
        )
        result.expect_no_code("NO_IMPLICIT_NET")

    def test_struct_field_member_access_does_not_orphan_the_struct_variable(self) -> None:
        """The regression this guards: treating `perms.u0`'s `perms` as a
        package-scope qualifier (see the test above) meant `perms` itself
        never got a use event recorded, so it looked undriven/unread even
        though it's plainly read and written via member access below."""
        result = run_inline_lint_case(
            {
                "top.sv": """
                package my_pkg;
                  typedef struct packed { logic u0; } perms_t;
                endpackage
                module top;
                  import my_pkg::*;
                  perms_t perms;
                  logic x;
                  always @* begin
                    perms.u0 = 1'b1;
                    x = perms.u0;
                  end
                endmodule
                """
            }
        )
        result.expect_no_code("NO_UNDRIVEN_SIGNAL")
        result.expect_no_code("READ_BEFORE_WRITE")

    def test_genuinely_undeclared_bare_name_is_still_implicit(self) -> None:
        """Package-scoping support must not weaken detection of an ordinary,
        unrelated undeclared identifier."""
        result = run_inline_lint_case(
            {
                "top.sv": """
                module top;
                  logic [7:0] x;
                  assign x = totally_undeclared;
                endmodule
                """
            }
        )
        result.expect_code_once("NO_IMPLICIT_NET")
