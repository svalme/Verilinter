from pathlib import Path

import pytest

import src.run_lint as run_lint_module
from src.pkg.rules.rule_selection import RuleSelection
from src.run_lint import main, run

DATA = Path(__file__).parent / "data" / "simple.v"
INITIAL_BLOCK_DATA = Path(__file__).parent / "data" / "initial_block.v"
FINAL_BLOCK_DATA = Path(__file__).parent / "data" / "final_block.v"
ALWAYS_FF_DATA = Path(__file__).parent / "data" / "always_ff.v"
ALWAYS_LATCH_DATA = Path(__file__).parent / "data" / "always_latch.v"
FOREVER_LOOP_DATA = Path(__file__).parent / "data" / "forever_loop.v"
REPEAT_LOOP_DATA = Path(__file__).parent / "data" / "repeat_loop.v"
WAIT_STATEMENT_DATA = Path(__file__).parent / "data" / "wait_statement.v"
WHILE_LOOP_DATA = Path(__file__).parent / "data" / "while_loop.v"
FOREACH_LOOP_DATA = Path(__file__).parent / "data" / "foreach_loop.v"
DO_WHILE_LOOP_DATA = Path(__file__).parent / "data" / "do_while_loop.v"
FOR_LOOP_DATA = Path(__file__).parent / "data" / "for_loop.v"
GENERATE_FOR_DATA = Path(__file__).parent / "data" / "generate_for.v"
IF_GENERATE_DATA = Path(__file__).parent / "data" / "if_generate.v"
TASK_DECLARATION_DATA = Path(__file__).parent / "data" / "task_declaration.v"
PROGRAM_DECLARATION_DATA = Path(__file__).parent / "data" / "program_declaration.sv"
CLOCKING_DECLARATION_DATA = Path(__file__).parent / "data" / "clocking_declaration.sv"
CHECKER_DECLARATION_DATA = Path(__file__).parent / "data" / "checker_declaration.sv"
INTERFACE_DECLARATION_DATA = Path(__file__).parent / "data" / "interface_declaration.sv"
MODPORT_DECLARATION_DATA = Path(__file__).parent / "data" / "modport_declaration.sv"
PACKAGE_DECLARATION_DATA = Path(__file__).parent / "data" / "package_declaration.sv"
DISABLE_STATEMENT_DATA = Path(__file__).parent / "data" / "disable_statement.v"
EVENT_TRIGGER_DATA = Path(__file__).parent / "data" / "event_trigger.v"
FORK_JOIN_DATA = Path(__file__).parent / "data" / "fork_join.v"
CASE_GENERATE_DATA = Path(__file__).parent / "data" / "case_generate.v"
CASE_INSIDE_DATA = Path(__file__).parent / "data" / "case_inside.v"
FULL_PARALLEL_CASE_DATA = Path(__file__).parent / "data" / "full_parallel_case.v"
INSIDE_OPERATOR_DATA = Path(__file__).parent / "data" / "inside_operator.v"
UNIQUE_PRIORITY_CASE_DATA = Path(__file__).parent / "data" / "unique_priority_case.v"
UNIQUE0_CASE_DATA = Path(__file__).parent / "data" / "unique0_case.v"
UNIQUE_IF_DATA = Path(__file__).parent / "data" / "unique_if.v"
PRIORITY_IF_DATA = Path(__file__).parent / "data" / "priority_if.v"
MULTIPLE_DRIVERS_DATA = Path(__file__).parent / "data" / "multiple_drivers.v"
INTERNAL_INOUT_DATA = Path(__file__).parent / "data" / "internal_inout.v"
UNDRIVEN_SIGNAL_DATA = Path(__file__).parent / "data" / "undriven_signal.v"
DEFAULT_NETTYPE_NONE_DATA = Path(__file__).parent / "data" / "default_nettype_none.v"
LATCH_IN_ALWAYS_COMB_DATA = Path(__file__).parent / "data" / "latch_in_always_comb.v"
DEFPARAM_USAGE_DATA = Path(__file__).parent / "data" / "defparam_usage.v"
FORCE_RELEASE_DATA = Path(__file__).parent / "data" / "force_release.v"
ASSIGN_DEASSIGN_DATA = Path(__file__).parent / "data" / "assign_deassign.v"
WAND_WOR_DATA = Path(__file__).parent / "data" / "wand_wor.v"
TRIREG_DATA = Path(__file__).parent / "data" / "trireg.v"
SUPPLY0_SUPPLY1_DATA = Path(__file__).parent / "data" / "supply0_supply1.v"
TRAN_RTRAN_DATA = Path(__file__).parent / "data" / "tran_rtran.v"
TRANIF_RTRANIF_DATA = Path(__file__).parent / "data" / "tranif_rtranif.v"
SPECIFY_BLOCK_DATA = Path(__file__).parent / "data" / "specify_block.v"
PRIMITIVE_DECLARATION_DATA = Path(__file__).parent / "data" / "primitive_declaration.v"
GATE_PRIMITIVE_DATA = Path(__file__).parent / "data" / "gate_primitive.v"
ALIAS_STATEMENT_DATA = Path(__file__).parent / "data" / "alias_statement.sv"
BIND_DIRECTIVE_DATA = Path(__file__).parent / "data" / "bind_directive.sv"
DELAY_CONTROL_DATA = Path(__file__).parent / "data" / "delay_control.v"
IMMEDIATE_ASSERTION_DATA = Path(__file__).parent / "data" / "immediate_assertion.sv"
CONCURRENT_ASSERTION_DATA = Path(__file__).parent / "data" / "concurrent_assertion.sv"
DISPLAY_SYSTEM_TASK_DATA = Path(__file__).parent / "data" / "display_system_task.v"
SIMULATION_CONTROL_TASK_DATA = Path(__file__).parent / "data" / "simulation_control_task.v"


class TestRunJobsValidation:
    def test_jobs_one_runs_sequentially(self) -> None:
        diagnostics = run([DATA], jobs=1)
        assert isinstance(diagnostics, list)

    def test_jobs_defaults_to_sequential(self) -> None:
        diagnostics = run([DATA])
        assert isinstance(diagnostics, list)

    def test_jobs_zero_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="jobs must be >= 1"):
            run([DATA], jobs=0)

    def test_jobs_negative_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="jobs must be >= 1"):
            run([DATA], jobs=-1)

    def test_jobs_above_one_raises_not_implemented(self) -> None:
        with pytest.raises(NotImplementedError, match="parallel linting"):
            run([DATA], jobs=2)

    def test_run_reports_initial_block_rule(self) -> None:
        diagnostics = run([INITIAL_BLOCK_DATA], jobs=1)

        assert any(d["code"] == "NO_INITIAL_BLOCK" for d in diagnostics)
        assert any("initial blocks" in d["message"] for d in diagnostics)

    def test_run_reports_final_block_rule(self) -> None:
        diagnostics = run([FINAL_BLOCK_DATA], jobs=1)

        assert any(d["code"] == "NO_FINAL_BLOCK" for d in diagnostics)
        assert any("final blocks" in d["message"] for d in diagnostics)

    def test_run_reports_always_latch_rule(self) -> None:
        diagnostics = run([ALWAYS_LATCH_DATA], jobs=1)

        assert any(d["code"] == "NO_ALWAYS_LATCH" for d in diagnostics)
        assert any("always_latch" in d["message"] for d in diagnostics)

    def test_run_reports_always_ff_rule(self) -> None:
        diagnostics = run([ALWAYS_FF_DATA], jobs=1)

        assert any(d["code"] == "NO_ALWAYS_FF" for d in diagnostics)
        assert any("always_ff" in d["message"] for d in diagnostics)

    def test_run_reports_forever_loop_rule(self) -> None:
        diagnostics = run([FOREVER_LOOP_DATA], jobs=1)

        assert any(d["code"] == "NO_FOREVER_LOOP" for d in diagnostics)
        assert any("forever loops" in d["message"] for d in diagnostics)

    def test_run_reports_repeat_loop_rule(self) -> None:
        diagnostics = run([REPEAT_LOOP_DATA], jobs=1)

        assert any(d["code"] == "NO_REPEAT_LOOP" for d in diagnostics)
        assert any("repeat loops" in d["message"] for d in diagnostics)

    def test_run_reports_wait_statement_rule(self) -> None:
        diagnostics = run([WAIT_STATEMENT_DATA], jobs=1)

        assert any(d["code"] == "NO_WAIT_STATEMENT" for d in diagnostics)
        assert any("wait statements" in d["message"] for d in diagnostics)

    def test_run_reports_while_loop_rule(self) -> None:
        diagnostics = run([WHILE_LOOP_DATA], jobs=1)

        assert any(d["code"] == "NO_WHILE_LOOP" for d in diagnostics)
        assert any("while loops" in d["message"] for d in diagnostics)

    def test_run_reports_foreach_loop_rule(self) -> None:
        diagnostics = run([FOREACH_LOOP_DATA], jobs=1)

        assert any(d["code"] == "NO_FOREACH_LOOP" for d in diagnostics)
        assert any("foreach loops" in d["message"] for d in diagnostics)

    def test_run_reports_do_while_loop_rule(self) -> None:
        diagnostics = run([DO_WHILE_LOOP_DATA], jobs=1)

        assert any(d["code"] == "NO_DO_WHILE_LOOP" for d in diagnostics)
        assert any("do-while loops" in d["message"] for d in diagnostics)

    def test_run_reports_for_loop_rule(self) -> None:
        diagnostics = run([FOR_LOOP_DATA], jobs=1)

        assert any(d["code"] == "NO_FOR_LOOP" for d in diagnostics)
        assert any("for loops" in d["message"] for d in diagnostics)

    def test_run_reports_generate_for_rule(self) -> None:
        diagnostics = run([GENERATE_FOR_DATA], jobs=1)

        assert any(d["code"] == "NO_GENERATE_FOR" for d in diagnostics)
        assert any("generate-for loops" in d["message"] for d in diagnostics)

    def test_run_reports_if_generate_rule(self) -> None:
        diagnostics = run([IF_GENERATE_DATA], jobs=1)

        assert any(d["code"] == "NO_IF_GENERATE" for d in diagnostics)
        assert any("if-generate" in d["message"] for d in diagnostics)

    def test_run_reports_task_declaration_rule(self) -> None:
        diagnostics = run([TASK_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_TASK_DECLARATION" for d in diagnostics)
        assert any("task declarations" in d["message"] for d in diagnostics)

    def test_run_reports_program_declaration_rule(self) -> None:
        diagnostics = run([PROGRAM_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_PROGRAM_DECLARATION" for d in diagnostics)
        assert any("program declarations" in d["message"] for d in diagnostics)

    def test_run_reports_clocking_declaration_rule(self) -> None:
        diagnostics = run([CLOCKING_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_CLOCKING_DECLARATION" for d in diagnostics)
        assert any("clocking declarations" in d["message"] for d in diagnostics)

    def test_run_reports_checker_declaration_rule(self) -> None:
        diagnostics = run([CHECKER_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_CHECKER_DECLARATION" for d in diagnostics)
        assert any("checker declarations" in d["message"] for d in diagnostics)

    def test_run_reports_interface_declaration_rule(self) -> None:
        diagnostics = run([INTERFACE_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_INTERFACE_DECLARATION" for d in diagnostics)
        assert any("interface declarations" in d["message"] for d in diagnostics)

    def test_run_reports_modport_declaration_rule(self) -> None:
        diagnostics = run([MODPORT_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_MODPORT_DECLARATION" for d in diagnostics)
        assert any("modport declarations" in d["message"] for d in diagnostics)

    def test_run_reports_package_declaration_rule(self) -> None:
        diagnostics = run([PACKAGE_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_PACKAGE_DECLARATION" for d in diagnostics)
        assert any("package declarations" in d["message"] for d in diagnostics)

    def test_run_reports_disable_statement_rule(self) -> None:
        diagnostics = run([DISABLE_STATEMENT_DATA], jobs=1)

        assert any(d["code"] == "NO_DISABLE_STATEMENT" for d in diagnostics)
        assert any("disable statements" in d["message"] for d in diagnostics)

    def test_run_reports_event_trigger_rule(self) -> None:
        diagnostics = run([EVENT_TRIGGER_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_EVENT_TRIGGER") == 2
        assert any("event trigger statements" in d["message"] for d in diagnostics)

    def test_run_reports_fork_join_rule(self) -> None:
        diagnostics = run([FORK_JOIN_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_FORK_JOIN") == 3
        assert any("fork/join style parallel blocks" in d["message"] for d in diagnostics)

    def test_run_reports_case_generate_rule(self) -> None:
        diagnostics = run([CASE_GENERATE_DATA], jobs=1)

        assert any(d["code"] == "NO_CASE_GENERATE" for d in diagnostics)
        assert any("case generate" in d["message"] for d in diagnostics)

    def test_run_reports_case_inside_rule(self) -> None:
        diagnostics = run([CASE_INSIDE_DATA], jobs=1)

        assert any(d["code"] == "NO_CASE_INSIDE" for d in diagnostics)
        assert any("case inside" in d["message"] for d in diagnostics)

    def test_run_reports_inside_operator_rule(self) -> None:
        diagnostics = run([INSIDE_OPERATOR_DATA], jobs=1)

        assert any(d["code"] == "NO_INSIDE_OPERATOR" for d in diagnostics)
        assert any("inside operator" in d["message"] for d in diagnostics)

    def test_run_reports_unique_priority_case_rule(self) -> None:
        diagnostics = run([UNIQUE_PRIORITY_CASE_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_UNIQUE_PRIORITY_CASE") == 2
        assert any("unique/priority case" in d["message"] for d in diagnostics)

    def test_run_reports_unique0_case_rule(self) -> None:
        diagnostics = run([UNIQUE0_CASE_DATA], jobs=1)

        assert any(d["code"] == "NO_UNIQUE0_CASE" for d in diagnostics)
        assert any("unique0 case" in d["message"] for d in diagnostics)

    def test_run_reports_unique_if_rule(self) -> None:
        diagnostics = run([UNIQUE_IF_DATA], jobs=1)

        assert any(d["code"] == "NO_UNIQUE_IF" for d in diagnostics)
        assert any("unique if" in d["message"] for d in diagnostics)

    def test_run_reports_priority_if_rule(self) -> None:
        diagnostics = run([PRIORITY_IF_DATA], jobs=1)

        assert any(d["code"] == "NO_PRIORITY_IF" for d in diagnostics)
        assert any("priority if" in d["message"] for d in diagnostics)

    def test_run_reports_full_parallel_case_rule(self) -> None:
        diagnostics = run([FULL_PARALLEL_CASE_DATA], jobs=1)

        assert any(d["code"] == "NO_FULL_PARALLEL_CASE" for d in diagnostics)
        assert any("full_case / parallel_case" in d["message"] for d in diagnostics)

    def test_run_reports_no_implicit_net_rule(self) -> None:
        diagnostics = run([DATA], jobs=1)

        assert any(d["code"] == "NO_IMPLICIT_NET" for d in diagnostics)
        assert any("Implicit net" in d["message"] for d in diagnostics)

    def test_run_reports_multiple_drivers_rule(self) -> None:
        diagnostics = run([MULTIPLE_DRIVERS_DATA], jobs=1)

        assert any(d["code"] == "NO_MULTIPLE_DRIVERS" for d in diagnostics)
        assert any("multiple drivers" in d["message"] for d in diagnostics)

    def test_run_reports_internal_inout_rule(self) -> None:
        diagnostics = run([INTERNAL_INOUT_DATA], jobs=1)

        assert any(d["code"] == "NO_INOUT_INTERNAL" for d in diagnostics)
        assert any("Internal inout" in d["message"] for d in diagnostics)

    def test_run_reports_undriven_signal_rule(self) -> None:
        diagnostics = run([UNDRIVEN_SIGNAL_DATA], jobs=1)

        assert any(d["code"] == "NO_UNDRIVEN_SIGNAL" for d in diagnostics)
        assert any("never driven" in d["message"] for d in diagnostics)

    def test_run_routes_default_nettype_none_to_undeclared_variable(self) -> None:
        diagnostics = run([DEFAULT_NETTYPE_NONE_DATA], jobs=1)

        assert any(d["code"] == "UNDECLARED_VARIABLE" for d in diagnostics)
        assert not any(d["code"] == "NO_IMPLICIT_NET" for d in diagnostics)

    def test_run_reports_latch_in_always_comb_rule(self) -> None:
        diagnostics = run([LATCH_IN_ALWAYS_COMB_DATA], jobs=1)

        assert any(d["code"] == "NO_LATCH_IN_ALWAYS_COMB" for d in diagnostics)
        assert any("latch-like storage" in d["message"] for d in diagnostics)

    def test_run_reports_defparam_rule(self) -> None:
        diagnostics = run([DEFPARAM_USAGE_DATA], jobs=1)

        assert any(d["code"] == "NO_DEFPARAM" for d in diagnostics)
        assert any("defparam" in d["message"] for d in diagnostics)

    def test_run_reports_force_release_rule(self) -> None:
        diagnostics = run([FORCE_RELEASE_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_FORCE_RELEASE") == 2
        assert any("force/release" in d["message"] for d in diagnostics)

    def test_run_reports_assign_deassign_rule(self) -> None:
        diagnostics = run([ASSIGN_DEASSIGN_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_ASSIGN_DEASSIGN") == 2
        assert any("assign/deassign" in d["message"] for d in diagnostics)

    def test_run_reports_wand_wor_rule(self) -> None:
        diagnostics = run([WAND_WOR_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_WAND_WOR") == 2
        assert any("wand/wor" in d["message"] for d in diagnostics)

    def test_run_reports_trireg_rule(self) -> None:
        diagnostics = run([TRIREG_DATA], jobs=1)

        assert any(d["code"] == "NO_TRIREG" for d in diagnostics)
        assert any("trireg" in d["message"] for d in diagnostics)

    def test_run_reports_supply0_supply1_rule(self) -> None:
        diagnostics = run([SUPPLY0_SUPPLY1_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_SUPPLY0_SUPPLY1") == 2
        assert any("supply0/supply1" in d["message"] for d in diagnostics)

    def test_run_reports_tran_rtran_rule(self) -> None:
        diagnostics = run([TRAN_RTRAN_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_TRAN_RTRAN") == 2
        assert any("tran/rtran" in d["message"] for d in diagnostics)

    def test_run_reports_tranif_rtranif_rule(self) -> None:
        diagnostics = run([TRANIF_RTRANIF_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_TRANIF_RTRANIF") == 4
        assert any("tranif/rtranif" in d["message"] for d in diagnostics)

    def test_run_reports_specify_block_rule(self) -> None:
        diagnostics = run([SPECIFY_BLOCK_DATA], jobs=1)

        assert any(d["code"] == "NO_SPECIFY_BLOCK" for d in diagnostics)
        assert any("specify block" in d["message"] for d in diagnostics)

    def test_run_reports_primitive_declaration_rule(self) -> None:
        diagnostics = run([PRIMITIVE_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_PRIMITIVE_DECLARATION" for d in diagnostics)
        assert any("primitive" in d["message"] for d in diagnostics)

    def test_run_reports_gate_primitive_rule(self) -> None:
        diagnostics = run([GATE_PRIMITIVE_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_GATE_PRIMITIVE") == 2
        assert any("gate-level primitives" in d["message"] for d in diagnostics)

    def test_run_reports_alias_statement_rule(self) -> None:
        diagnostics = run([ALIAS_STATEMENT_DATA], jobs=1)

        assert any(d["code"] == "NO_ALIAS_STATEMENT" for d in diagnostics)
        assert any("alias statement" in d["message"] for d in diagnostics)

    def test_run_reports_bind_directive_rule(self) -> None:
        diagnostics = run([BIND_DIRECTIVE_DATA], jobs=1)

        assert any(d["code"] == "NO_BIND_DIRECTIVE" for d in diagnostics)
        assert any("bind directive" in d["message"] for d in diagnostics)
        assert not any(d["code"] == "NO_IMPLICIT_NET" for d in diagnostics)

    def test_run_reports_delay_control_rule(self) -> None:
        diagnostics = run([DELAY_CONTROL_DATA], jobs=1)

        assert any(d["code"] == "NO_DELAY_CONTROL" for d in diagnostics)
        assert any("delay control" in d["message"] for d in diagnostics)

    def test_run_reports_immediate_assertion_rule(self) -> None:
        diagnostics = run([IMMEDIATE_ASSERTION_DATA], jobs=1)

        assert any(d["code"] == "NO_IMMEDIATE_ASSERTION" for d in diagnostics)
        assert any("immediate assertions" in d["message"] for d in diagnostics)

    def test_run_reports_concurrent_assertion_rule(self) -> None:
        diagnostics = run([CONCURRENT_ASSERTION_DATA], jobs=1)

        assert any(d["code"] == "NO_CONCURRENT_ASSERTION" for d in diagnostics)
        assert any("concurrent assertions" in d["message"] for d in diagnostics)

    def test_run_reports_display_system_task_rule(self) -> None:
        diagnostics = run([DISPLAY_SYSTEM_TASK_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_DISPLAY_SYSTEM_TASK") == 2
        assert any("$display" in d["message"] for d in diagnostics)

    def test_run_reports_simulation_control_task_rule(self) -> None:
        diagnostics = run([SIMULATION_CONTROL_TASK_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_SIMULATION_CONTROL_TASK") == 2
        assert any("$stop" in d["message"] for d in diagnostics)

    def test_run_uses_parser_boundary_parse_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        first = DATA
        second = INITIAL_BLOCK_DATA
        parse_calls: list[str] = []
        walked_roots: list[tuple[object, object, bool]] = []

        class FakeTree:
            def __init__(self, path: str) -> None:
                self.path = path
                self.root = object()

        def fake_parse_file(path: str) -> FakeTree:
            parse_calls.append(path)
            return FakeTree(path)

        class FakeWalker:
            def __init__(self, dispatch: object) -> None:
                self.dispatch = dispatch

            def walk(
                self,
                root: object,
                tree: FakeTree,
                _ctx: object,
                symbol_table: object,
                on_node: object | None = None,
            ) -> None:
                walked_roots.append((root, tree, on_node is not None))
                assert root is tree.root
                assert getattr(symbol_table, "current_file", None) == tree.path

        monkeypatch.setattr(run_lint_module, "parse_file", fake_parse_file)
        monkeypatch.setattr(run_lint_module, "file_uses_default_nettype_none", lambda path: False)
        monkeypatch.setattr(run_lint_module, "Walker", FakeWalker)
        monkeypatch.setattr(
            run_lint_module.symbol_rule_runner,
            "run",
            lambda symbol_table, _selection=None: [],
        )
        monkeypatch.setattr(
            run_lint_module.module_rule_runner,
            "run",
            lambda symbol_table, _selection=None: [],
        )

        diagnostics = run([first, second], jobs=1)

        assert diagnostics == []
        assert parse_calls == [str(first), str(second)]
        assert len(walked_roots) == 2
        assert all(root is tree.root for root, tree, _has_callback in walked_roots)
        assert all(has_callback for _root, _tree, has_callback in walked_roots)

    def test_run_aggregates_multi_file_diagnostics_after_shared_walk(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        first = DATA
        second = INITIAL_BLOCK_DATA
        parse_calls: list[str] = []
        walked_paths: list[str] = []

        class FakeTree:
            def __init__(self, path: str) -> None:
                self.path = path
                self.root = object()

        def fake_parse_file(path: str) -> FakeTree:
            parse_calls.append(path)
            return FakeTree(path)

        class FakeWalker:
            def __init__(self, dispatch: object) -> None:
                self.dispatch = dispatch

            def walk(
                self,
                root: object,
                tree: FakeTree,
                _ctx: object,
                symbol_table: object,
                on_node: object | None = None,
            ) -> None:
                walked_paths.append(tree.path)
                assert root is tree.root
                assert getattr(symbol_table, "current_file", None) == tree.path
                assert on_node is not None
                on_node(
                    type(
                        "FakeVNode",
                        (),
                        {"location": {"line": 1, "col": 1, "file": tree.path}},
                    )(),
                    object(),
                )

        def fake_rule_check(
            vnode: object,
            _ctx: object,
            _selection: RuleSelection | None = None,
        ) -> list[dict[str, object]]:
            location = getattr(vnode, "location")
            return [
                {
                    "code": "AST_FAKE",
                    "line": location["line"],
                    "col": location["col"],
                    "file": location["file"],
                    "message": "ast diagnostic",
                }
            ]

        monkeypatch.setattr(run_lint_module, "parse_file", fake_parse_file)
        monkeypatch.setattr(run_lint_module, "file_uses_default_nettype_none", lambda path: False)
        monkeypatch.setattr(run_lint_module, "Walker", FakeWalker)
        monkeypatch.setattr(run_lint_module.rule_runner, "check", fake_rule_check)
        monkeypatch.setattr(
            run_lint_module.symbol_rule_runner,
            "run",
            lambda symbol_table, _selection=None: [
                {
                    "code": "SYMBOL_FAKE",
                    "line": 2,
                    "col": 1,
                    "file": getattr(symbol_table, "current_file"),
                    "message": f"symbol diagnostic after {len(getattr(symbol_table, 'modules', {}))} modules",
                }
            ],
        )
        monkeypatch.setattr(
            run_lint_module.module_rule_runner,
            "run",
            lambda _symbol_table, _selection=None: [
                {
                    "code": "MODULE_FAKE",
                    "line": 3,
                    "col": 1,
                    "file": str(second),
                    "message": "module diagnostic",
                }
            ],
        )

        diagnostics = run([first, second], jobs=1)

        assert parse_calls == [str(first), str(second)]
        assert walked_paths == [str(first), str(second)]
        assert [d["code"] for d in diagnostics] == [
            "AST_FAKE",
            "AST_FAKE",
            "SYMBOL_FAKE",
            "MODULE_FAKE",
        ]
        assert diagnostics[0]["file"] == str(first)
        assert diagnostics[1]["file"] == str(second)
        assert diagnostics[2]["file"] == str(second)
        assert diagnostics[3]["file"] == str(second)


class TestMain:
    def test_main_returns_zero_for_valid_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = main([str(DATA)])

        captured = capsys.readouterr()
        assert result == 0
        assert captured.err == ""

    def test_main_returns_one_for_missing_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = main(["does_not_exist.v"])

        captured = capsys.readouterr()
        assert result == 1
        assert "file not found" in captured.err

    def test_main_prints_no_issues_when_clean(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("src.run_lint.run", lambda paths, jobs=1: [])

        result = main([str(DATA)])

        captured = capsys.readouterr()
        assert result == 0
        assert "No issues found." in captured.out

    def test_main_prints_diagnostics(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "src.run_lint.run",
            lambda paths, jobs=1: [
                {"code": "UNUSED_VARIABLE", "line": 3, "col": 7, "message": "Example diagnostic", "file": "demo.sv"}
            ],
        )

        result = main([str(DATA)])

        captured = capsys.readouterr()
        assert result == 0
        assert "demo.sv:3:7" in captured.out
        assert "Example diagnostic" in captured.out
        assert "[UNUSED_VARIABLE]" in captured.out

    def test_main_prints_multiple_diagnostics(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "src.run_lint.run",
            lambda paths, jobs=1: [
                {"code": "FIRST", "line": 3, "col": 7, "message": "First diagnostic", "file": "demo_a.sv"},
                {"code": "SECOND", "line": 8, "col": 2, "message": "Second diagnostic", "file": "demo_b.sv"},
            ],
        )

        result = main([str(DATA)])

        captured = capsys.readouterr()
        assert result == 0
        assert "demo_a.sv:3:7 - [FIRST] First diagnostic" in captured.out
        assert "demo_b.sv:8:2 - [SECOND] Second diagnostic" in captured.out


class TestRunRuleSelection:
    def test_run_passes_rule_selection_to_all_runners(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        selection = RuleSelection(enabled_categories=frozenset({"sv_subset"}))
        seen: dict[str, object] = {}

        class FakeTree:
            def __init__(self, path: str) -> None:
                self.path = path
                self.root = object()

        def fake_parse_file(path: str) -> FakeTree:
            return FakeTree(path)

        class FakeWalker:
            def __init__(self, dispatch: object) -> None:
                self.dispatch = dispatch

            def walk(
                self,
                root: object,
                tree: FakeTree,
                _ctx: object,
                symbol_table: object,
                on_node: object | None = None,
            ) -> None:
                assert root is tree.root
                assert getattr(symbol_table, "current_file", None) == tree.path
                assert on_node is not None
                on_node(type("FakeVNode", (), {"location": {"line": 1, "col": 1, "file": tree.path}})(), object())

        def fake_rule_check(
            vnode: object,
            ctx: object,
            passed_selection: RuleSelection | None = None,
        ) -> list[dict[str, object]]:
            seen["syntax"] = passed_selection
            return []

        def fake_symbol_run(
            symbol_table: object,
            passed_selection: RuleSelection | None = None,
        ) -> list[dict[str, object]]:
            seen["symbol"] = passed_selection
            return []

        def fake_module_run(
            symbol_table: object,
            passed_selection: RuleSelection | None = None,
        ) -> list[dict[str, object]]:
            seen["module"] = passed_selection
            return []

        monkeypatch.setattr(run_lint_module, "parse_file", fake_parse_file)
        monkeypatch.setattr(run_lint_module, "file_uses_default_nettype_none", lambda path: False)
        monkeypatch.setattr(run_lint_module, "Walker", FakeWalker)
        monkeypatch.setattr(run_lint_module.rule_runner, "check", fake_rule_check)
        monkeypatch.setattr(run_lint_module.symbol_rule_runner, "run", fake_symbol_run)
        monkeypatch.setattr(run_lint_module.module_rule_runner, "run", fake_module_run)

        diagnostics = run([DATA], jobs=1, rule_selection=selection)

        assert diagnostics == []
        assert seen == {
            "syntax": selection,
            "symbol": selection,
            "module": selection,
        }
