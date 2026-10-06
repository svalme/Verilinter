import pytest

from tests.support.lint_harness import run_inline_lint_case


def machine(reset_assignment="state <= 3'b001;", default="", sequential="state <= next_state;", style="always_comb"):
    return f"""
        module m(input clk, rst, advance);
        logic [2:0] state, next_state;
        always @(posedge clk or posedge rst)
            if (rst) begin {reset_assignment} end else begin {sequential} end
        {style} begin
            next_state = state;
            case (state)
                3'b001: if (advance) next_state = 3'b010;
                3'b010: next_state = 3'b011;
                3'b011: next_state = 3'b001;
                {default}
            endcase
        end
        endmodule
    """


@pytest.mark.parametrize("style", ["always_comb", "always @*"])
def test_recognizes_two_process_fsm(style):
    result = run_inline_lint_case({"fsm.sv": machine(style=style)})
    result.expect_code_once("MISSING_DEFAULT_ON_STATE_CASE")
    result.expect_code_once("ONE_HOT_ENCODING_VIOLATION")
    result.expect_no_code("MISSING_STATE_REGISTER_RESET")


def test_checks_reset_in_sequential_block():
    result = run_inline_lint_case({"fsm.sv": machine(reset_assignment="next_state <= 0;")})
    # This also creates a second next-state writer and is intentionally skipped.
    result.expect_no_code("MISSING_STATE_REGISTER_RESET")
    result = run_inline_lint_case({"fsm.sv": machine(reset_assignment=";")})
    result.expect_code_once("MISSING_STATE_REGISTER_RESET")


def test_accepts_default_and_valid_encoding():
    source = machine(default="default: next_state = 3'b001;").replace("3'b011", "3'b100")
    result = run_inline_lint_case({"fsm.sv": source})
    for code in ("MISSING_DEFAULT_ON_STATE_CASE", "ONE_HOT_ENCODING_VIOLATION", "MISSING_STATE_REGISTER_RESET"):
        result.expect_no_code(code)


def test_unlinked_mux_is_not_fsm():
    result = run_inline_lint_case({"fsm.sv": machine(sequential="state <= 3'b001;")})
    result.expect_no_code("MISSING_DEFAULT_ON_STATE_CASE")
    result.expect_no_code("ONE_HOT_ENCODING_VIOLATION")


def test_ambiguous_state_writers_are_skipped():
    source = machine().replace("endmodule", "always @(negedge clk) state <= next_state; endmodule")
    result = run_inline_lint_case({"fsm.sv": source})
    result.expect_no_code("MISSING_DEFAULT_ON_STATE_CASE")


def test_local_shadow_is_not_correlated_with_module_register():
    source = machine().replace("next_state = state;", "logic [2:0] state; next_state = state;")
    result = run_inline_lint_case({"fsm.sv": source})
    result.expect_no_code("MISSING_DEFAULT_ON_STATE_CASE")


def test_model_records_states_transitions_guards_and_reset():
    from src.pkg.parser.parse import parse_text
    from src.pkg.parser.syntax import state_machine_model
    from src.pkg.semantic.symbol_table import SymbolTable
    from src.pkg.walk.context import Context
    from src.pkg.walk.dispatch import dispatch
    from src.pkg.walk.walker import Walker

    table = SymbolTable()
    tree = parse_text(machine())
    walker = Walker(dispatch)
    walker.walk(tree.root, tree, Context(scope=table.global_scope), table)
    models = [model for vnode, ctx in walker.results
              if (model := state_machine_model(vnode.raw, ctx)) is not None]
    assert len(models) == 1
    model = models[0]
    assert model.state_name == "state"
    assert model.next_state_name == "next_state"
    assert model.legal_states == frozenset((1, 2, 3))
    assert [(t.sources, t.destination) for t in model.transitions] == [((1,), 2), ((2,), 3), ((3,), 1)]
    assert len(model.transitions[0].guards) == 1
    assert model.transitions[0].guards[0][1] is True
    assert model.reset_covered
    module_scopes = [child for child in table.global_scope.children if child.kind == "module"]
    assert len(module_scopes) == 1
    assert module_scopes[0].fsm_models == [model]
