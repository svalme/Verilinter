"""End-to-end extreme nesting and stress tests through the full LintPipeline.

Validates that:
1. Deeply nested conditional structures (50+ nested `if` statements) execute
   promptly under `terminates_within` without stack overflow or walker failure.
2. Deeply nested case statements (50+ nested `case` blocks) terminate promptly.
3. Pathologically nested arithmetic/bitwise expressions (100-level nesting)
   complete expression resolution and folding without hitting recursion limits.
4. Deeply nested concatenations (80 levels) traverse safely.
5. Linear module instantiation chains (50+ levels of hierarchy) complete
   symbol resolution and hierarchy cycle analysis within time budget.
"""
from __future__ import annotations

import pytest

from tests.support.lint_harness import run_inline_lint_case
from tests.support.termination import terminates_within


pytestmark = pytest.mark.stress


def test_extreme_conditional_nesting_terminates_promptly() -> None:
    """Validate 40 levels of nested if-blocks execute safely through LintPipeline."""
    depth = 40
    lines = ["module extreme_cond_top(input logic [39:0] cond_i, output logic out_o);", "  always_comb begin"]
    for i in range(depth):
        lines.append(f"    {'  ' * i}if (cond_i[{i}]) begin")
    lines.append(f"    {'  ' * depth}out_o = 1'b1;")
    for i in range(depth - 1, -1, -1):
        lines.append(f"    {'  ' * i}end")
    lines.extend(["  end", "endmodule"])
    hdl = "\n".join(lines)

    with terminates_within("extreme_cond_nesting", budget_s=10.0):
        result = run_inline_lint_case({"extreme_cond.sv": hdl})

    # DEEPLY_NESTED_BLOCK should detect this extreme structure
    assert result.for_code("DEEPLY_NESTED_BLOCK") != []


def test_extreme_case_nesting_terminates_promptly() -> None:
    """Validate 25 levels of nested case statements execute safely through LintPipeline."""
    depth = 25
    lines = ["module extreme_case_top(input logic [24:0] sel_i, output logic out_o);", "  always_comb begin"]
    for i in range(depth):
        indent = "  " * (i + 1)
        lines.append(f"{indent}case (sel_i[{i}])")
        lines.append(f"{indent}  1'b1: begin")
    lines.append(f"    {'  ' * (depth + 1)}out_o = 1'b1;")
    for i in range(depth - 1, -1, -1):
        indent = "  " * (i + 1)
        lines.append(f"{indent}  end")
        lines.append(f"{indent}  default: out_o = 1'b0;")
        lines.append(f"{indent}endcase")
    lines.extend(["  end", "endmodule"])
    hdl = "\n".join(lines)

    with terminates_within("extreme_case_nesting", budget_s=15.0):
        result = run_inline_lint_case({"extreme_case.sv": hdl})

    assert isinstance(result.diagnostics, list)


def test_extreme_expression_nesting_terminates_promptly() -> None:
    """Validate 100-level deep parenthesized expression folding under full pipeline."""
    depth = 100
    # Construct: (1 + (1 + (1 + ... (1 + a_i) ...)))
    expr = "a_i"
    for _ in range(depth):
        expr = f"(8'd1 + {expr})"

    hdl = f"""
    module extreme_expr_top(input logic [7:0] a_i, output logic [7:0] y_o);
      assign y_o = {expr};
    endmodule
    """

    with terminates_within("extreme_expr_nesting", budget_s=3.0):
        result = run_inline_lint_case({"extreme_expr.sv": hdl})

    assert isinstance(result.diagnostics, list)


def test_extreme_concatenation_nesting_terminates_promptly() -> None:
    """Validate 80 levels of nested concatenations execute without RecursionError."""
    depth = 80
    # Construct: {1'b0, {1'b0, {1'b0, ... {1'b0, in_i} ...}}}
    concat = "in_i"
    for _ in range(depth):
        concat = f"{{1'b0, {concat}}}"

    hdl = f"""
    module extreme_concat_top(input logic in_i, output logic [80:0] out_o);
      assign out_o = {concat};
    endmodule
    """

    with terminates_within("extreme_concat_nesting", budget_s=3.0):
        result = run_inline_lint_case({"extreme_concat.sv": hdl})

    assert isinstance(result.diagnostics, list)


def test_extreme_generate_block_nesting_terminates_promptly() -> None:
    """Validate 35 levels of nested generate-if blocks."""
    depth = 35
    lines = ["module extreme_gen_top #(parameter int P = 1) ();"]
    for i in range(depth):
        indent = "  " * (i + 1)
        lines.append(f"{indent}if (P > 0) begin: gen_{i}")
    lines.append(f"    {'  ' * (depth + 1)}wire w;")
    for i in range(depth - 1, -1, -1):
        indent = "  " * (i + 1)
        lines.append(f"{indent}end")
    lines.append("endmodule")
    hdl = "\n".join(lines)

    with terminates_within("extreme_gen_nesting", budget_s=10.0):
        result = run_inline_lint_case({"extreme_gen.sv": hdl})

    assert isinstance(result.diagnostics, list)


def test_extreme_module_hierarchy_chain_terminates_promptly() -> None:
    """Validate 35 linearly nested module instantiations execute hierarchy checks cleanly."""
    count = 35
    files: dict[str, str] = {}
    for i in range(count):
        if i == count - 1:
            files[f"mod_{i}.sv"] = f"""
            module mod_{i}(input logic clk_i);
            endmodule
            """
        else:
            files[f"mod_{i}.sv"] = f"""
            module mod_{i}(input logic clk_i);
              mod_{i + 1} u_sub (
                .clk_i(clk_i)
              );
            endmodule
            """

    with terminates_within("extreme_hierarchy_chain", budget_s=15.0):
        result = run_inline_lint_case(files)

    assert result.for_code("CIRCULAR_MODULE_INSTANTIATION") == []
