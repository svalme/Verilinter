import pytest

from tests.support.lint_harness import run_inline_lint_case as _run


def run_inline_lint_case(source):
    return _run({"coverage.sv": source})


@pytest.mark.parametrize("rhs, expected", [
    ("a * (b + c)", 1),
    ("(a * b) * c", 1),
    ("sel ? a * b : c", 1),
    ("a * unknown", 0),
    ("$unsigned(a * b)", 0),
    ("sel ? a : c", 0),
])
def test_arithmetic_capacity_and_boundaries(rhs, expected):
    result = run_inline_lint_case(f"""
        module m(input [7:0] a,b,c, input sel, output [7:0] p);
        assign p = {rhs}; endmodule
    """)
    result.expect_code_count("ARITHMETIC_RESULT_TRUNCATION", expected)


@pytest.mark.parametrize("vehicle", [
    "assign p = a * b;",
    "always @* p = a * b;",
    "always @(posedge clk) p <= a * b;",
    "wire [7:0] q = a * b;",
    "assign p[7:0] = a * b;",
    "assign {p[3:0], p[7:4]} = a * b;",
])
def test_arithmetic_assignment_vehicles(vehicle):
    result = run_inline_lint_case(f"""
        module m(input clk, input [7:0] a,b);
        reg [7:0] p; {vehicle} endmodule
    """)
    result.expect_code_once("ARITHMETIC_RESULT_TRUNCATION")


@pytest.mark.parametrize("rhs, signed_count", [
    ("$signed(a)", 0), ("$unsigned(s)", 0),
    ("$unsigned($signed(a))", 0),
])
def test_cast_signedness(rhs, signed_count):
    result = run_inline_lint_case(f"""
        module m(input [7:0] a, input signed [7:0] s, output [7:0] p);
        assign p = {rhs}; endmodule
    """)
    result.expect_code_count("ASSIGNMENT_SIGNEDNESS_MISMATCH", signed_count)


def test_explicit_cast_widening_preserves_intent():
    result = run_inline_lint_case("""
        module m(input [3:0] a, output [7:0] p, q);
        assign p = $signed(a);
        assign q = $signed(a) >>> 1;
        endmodule
    """)
    for code in ("ASSIGNMENT_WIDTH_MISMATCH", "ASSIGNMENT_SIGNEDNESS_MISMATCH"):
        result.expect_no_code(code)


def test_explicit_cast_still_reports_narrowing():
    result = run_inline_lint_case("""
        module m(input [7:0] a, output [3:0] p);
        assign p = $signed(a); endmodule
    """)
    result.expect_code_once("ASSIGNMENT_TRUNCATION")


def test_ternary_common_width():
    result = run_inline_lint_case("""
        module m(input sel, input [7:0] a, input [3:0] b, output [3:0] p);
        assign p = sel ? a : b; endmodule
    """)
    result.expect_code_once("ASSIGNMENT_TRUNCATION")


def test_port_default_is_checked():
    result = run_inline_lint_case("module m(input [3:0] a = 8'hff); endmodule")
    result.expect_code_once("ASSIGNMENT_TRUNCATION")


@pytest.mark.parametrize("declaration", ["wire [7:0] p = 5;", "logic [7:0] p = 5;", "input [7:0] p = 5"])
def test_unsized_initializers(declaration):
    source = f"module m({declaration}); endmodule" if declaration.startswith("input") else f"module m; {declaration} endmodule"
    run_inline_lint_case(source).expect_code_once("NO_UNSIZED_LITERAL")


def test_unsized_definition_values_are_not_assignment_policy():
    result = run_inline_lint_case("""
        package definitions;
        parameter int WIDTH = 8;
        typedef enum integer {IDLE = 0, RUN = 1, DONE = 2} state_t;
        endpackage
    """)
    result.expect_no_code("NO_UNSIZED_LITERAL")


def test_compound_assignments_do_not_compare_rhs_as_value_transfer():
    result = run_inline_lint_case("""
        module m(input [3:0] a); logic [7:0] p;
        initial begin p += a; p += p; p <<= a; end
        endmodule
    """)
    for code in ("ASSIGNMENT_WIDTH_MISMATCH", "ASSIGNMENT_SIGNEDNESS_MISMATCH", "ASSIGNMENT_TRUNCATION", "NO_SELF_ASSIGNMENT"):
        result.expect_no_code(code)


@pytest.mark.parametrize("vehicle", ["assign p = a;", "always @* p = a;", "always @(posedge clk) p <= a;", "wire [3:0] q = a;", "assign p[3:0] = a;", "assign {p[1:0], p[3:2]} = a;"])
def test_width_assignment_vehicles(vehicle):
    result = run_inline_lint_case(f"module m(input clk, input [7:0] a); reg [3:0] p; {vehicle} endmodule")
    result.expect_code_once("ASSIGNMENT_TRUNCATION")


def test_literal_overflow_in_initializers_and_port_defaults():
    result = run_inline_lint_case("module m(input [3:0] a = 4'hff); wire [3:0] b = 4'hff; endmodule")
    result.expect_code_count("LITERAL_WIDTH_OVERFLOW", 2)


@pytest.mark.parametrize("expression, operand, capacity", [
    ("a * b", (8, False), (16, False)),
    ("(a * b) * b", (8, False), (24, False)),
    ("$signed(a * b)", (8, True), (8, True)),
    ("$unsigned($signed(a))", (8, False), (8, False)),
    ("a ? a * b : b", (8, False), (16, False)),
    ("a * missing", (None, None), (None, None)),
])
def test_language_width_is_separate_from_product_capacity(expression, operand, capacity):
    from types import SimpleNamespace
    from src.pkg.parser.parse import parse_text
    from src.pkg.parser.syntax import expression_width_and_signed, natural_expression_width_and_signed

    scope = {name: SimpleNamespace(bit_width=8, is_signed=False) for name in ("a", "b")}
    tree = parse_text(expression)
    assert expression_width_and_signed(scope, tree.root, tree) == operand
    assert natural_expression_width_and_signed(scope, tree.root, tree) == capacity


def test_grouped_ansi_types_preserve_width_sign_and_direction_boundaries():
    from src.pkg.engine import LintPipeline
    from src.pkg.parser.parse import parse_text

    tree = parse_text("""
        module m(input logic signed [7:0] a, b,
                 output [3:0] p, q, output scalar,
                 input int count, limit);
        endmodule
    """)
    result = LintPipeline().analyze_trees([("types.sv", tree)])
    symbols = result.symbol_table.modules["m"][0].symbols
    assert (symbols["b"].bit_width, symbols["b"].is_signed, symbols["b"].port_direction) == (8, True, "input")
    assert (symbols["q"].bit_width, symbols["q"].is_signed, symbols["q"].port_direction) == (4, False, "output")
    assert symbols["scalar"].bit_width == 1
    assert (symbols["limit"].bit_width, symbols["limit"].is_signed) == (32, True)
    assert symbols["b"].packed_dimension_widths == [8]
    assert (symbols["b"].msb, symbols["b"].lsb) == (7, 0)
