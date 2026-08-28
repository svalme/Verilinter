from pathlib import Path

import pytest

import src.run_lint as run_lint_module
from src.pkg.rules.rule_selection import RuleSelection
from src.run_lint import collect_paths, main, run

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
GENERATE_BLOCK_MISSING_LABEL_DATA = Path(__file__).parent / "data" / "generate_block_missing_label.v"
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
CLASS_DECLARATION_DATA = Path(__file__).parent / "data" / "class_declaration.sv"
COVERGROUP_DECLARATION_DATA = Path(__file__).parent / "data" / "covergroup_declaration.sv"
SEQUENCE_DECLARATION_DATA = Path(__file__).parent / "data" / "sequence_declaration.sv"
PROPERTY_DECLARATION_DATA = Path(__file__).parent / "data" / "property_declaration.sv"
FUNCTION_DECLARATION_DATA = Path(__file__).parent / "data" / "function_declaration.sv"
UWIRE_DATA = Path(__file__).parent / "data" / "uwire.v"
READ_BEFORE_WRITE_DATA = Path(__file__).parent / "data" / "read_before_write.v"
INPUT_PORT_WRITE_DATA = Path(__file__).parent / "data" / "input_port_write.v"
WRITE_ONLY_VARIABLE_DATA = Path(__file__).parent / "data" / "write_only_variable.v"
MIXED_ASSIGNMENT_STYLE_DATA = Path(__file__).parent / "data" / "mixed_assignment_style.v"
NAMED_TYPE_REFERENCE_DATA = Path(__file__).parent / "data" / "named_type_reference.sv"
INVOCATION_CALLEE_DATA = Path(__file__).parent / "data" / "invocation_callee.sv"
COVER_CROSS_DATA = Path(__file__).parent / "data" / "cover_cross.sv"
EXTENDS_CLAUSE_DATA = Path(__file__).parent / "data" / "extends_clause.sv"
SELF_ASSIGNMENT_DATA = Path(__file__).parent / "data" / "self_assignment.v"
MULTIPLE_NONBLOCKING_WRITES_DATA = Path(__file__).parent / "data" / "multiple_nonblocking_writes.v"
DUPLICATE_CASE_ITEM_DATA = Path(__file__).parent / "data" / "duplicate_case_item.v"
PORT_CONNECTION_ISSUES_DATA = Path(__file__).parent / "data" / "port_connection_issues.sv"
PORT_CONNECTION_ADVANCED_DATA = Path(__file__).parent / "data" / "port_connection_advanced.sv"
WILDCARD_PORT_CONNECTION_DATA = Path(__file__).parent / "data" / "wildcard_port_connection.sv"
UNDEFINED_MODULE_PARAM_OVERRIDE_DATA = Path(__file__).parent / "data" / "undefined_module_param_override.sv"
LET_DECLARATION_DATA = Path(__file__).parent / "data" / "let_declaration.sv"
CONFIG_DECLARATION_DATA = Path(__file__).parent / "data" / "config_declaration.v"
RANDSEQUENCE_DATA = Path(__file__).parent / "data" / "randsequence.sv"
EXPECT_RESTRICT_PROPERTY_DATA = Path(__file__).parent / "data" / "expect_restrict_property.sv"
VIRTUAL_INTERFACE_DATA = Path(__file__).parent / "data" / "virtual_interface.sv"
DPI_IMPORT_EXPORT_DATA = Path(__file__).parent / "data" / "dpi_import_export.sv"
REAL_TYPE_DATA = Path(__file__).parent / "data" / "real_type.v"
STRING_TYPE_DATA = Path(__file__).parent / "data" / "string_type.sv"
CHANDLE_TYPE_DATA = Path(__file__).parent / "data" / "chandle_type.sv"
RANDOM_SYSTEM_FUNCTION_DATA = Path(__file__).parent / "data" / "random_system_function.v"
TIME_SYSTEM_FUNCTION_DATA = Path(__file__).parent / "data" / "time_system_function.v"
NONBLOCKING_COMBINATIONAL_DATA = Path(__file__).parent / "data" / "nonblocking_combinational.v"
VCD_DUMP_TASK_DATA = Path(__file__).parent / "data" / "vcd_dump_task.v"
FILE_IO_SYSTEM_TASK_DATA = Path(__file__).parent / "data" / "file_io_system_task.v"
PLUSARGS_SYSTEM_FUNCTION_DATA = Path(__file__).parent / "data" / "plusargs_system_function.v"
ASSERTION_CONTROL_TASK_DATA = Path(__file__).parent / "data" / "assertion_control_task.sv"
QUEUE_DATA = Path(__file__).parent / "data" / "queue.sv"
DYNAMIC_ARRAY_DATA = Path(__file__).parent / "data" / "dynamic_array.sv"
ASSOCIATIVE_ARRAY_DATA = Path(__file__).parent / "data" / "associative_array.sv"
BLOCKING_COMBINATIONAL_OK_DATA = Path(__file__).parent / "data" / "blocking_combinational_ok.v"
UNIQUE0_IF_DATA = Path(__file__).parent / "data" / "unique0_if.v"
SWITCH_PRIMITIVE_DATA = Path(__file__).parent / "data" / "switch_primitive.v"
UNUSED_PARAMETER_DATA = Path(__file__).parent / "data" / "unused_parameter.v"
UNSIZED_LITERAL_DATA = Path(__file__).parent / "data" / "unsized_literal.v"
IF_WITHOUT_BEGIN_END_DATA = Path(__file__).parent / "data" / "if_without_begin_end.v"
MISSING_TIMESCALE_DIRECTIVE_DATA = Path(__file__).parent / "data" / "missing_timescale_directive.v"
HAS_TIMESCALE_DIRECTIVE_DATA = Path(__file__).parent / "data" / "has_timescale_directive.v"


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

    def test_jobs_above_one_runs_with_parallel_worker_path(self) -> None:
        diagnostics = run([DATA], jobs=2)

        assert isinstance(diagnostics, list)

    def test_collect_paths_deduplicates_overlapping_inputs(self) -> None:
        paths = collect_paths(["tests/data", "tests/data/self_assignment.v"])

        self_assignment_matches = [path for path in paths if path.name == "self_assignment.v"]
        assert len(self_assignment_matches) == 1

    def test_run_does_not_duplicate_diagnostics_for_overlapping_inputs(self) -> None:
        paths = collect_paths(["tests/data", "tests/data/self_assignment.v"])
        diagnostics = run(paths, jobs=1)

        matching = [
            diagnostic
            for diagnostic in diagnostics
            if diagnostic["code"] == "NO_SELF_ASSIGNMENT"
            and str(diagnostic.get("file", "")).endswith("self_assignment.v")
        ]
        assert len(matching) == 1

    def test_run_rejects_rule_selection_and_profile_together(self) -> None:
        with pytest.raises(ValueError, match="either rule_selection or rule_profile"):
            run(
                [DATA],
                jobs=1,
                rule_selection=RuleSelection(enabled_profiles=frozenset({"rtl_strict"})),
                rule_profile="rtl_strict",
            )

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
        assert not any(d["code"] == "READ_BEFORE_WRITE" for d in diagnostics)

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

    def test_run_reports_missing_generate_block_label_rule(self) -> None:
        diagnostics = run([GENERATE_BLOCK_MISSING_LABEL_DATA], jobs=1)

        assert any(d["code"] == "MISSING_GENERATE_BLOCK_LABEL" for d in diagnostics)
        assert any("missing an explicit label" in d["message"] for d in diagnostics)

    def test_run_reports_task_declaration_rule(self) -> None:
        diagnostics = run([TASK_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_TASK_DECLARATION" for d in diagnostics)
        assert any("task declarations" in d["message"] for d in diagnostics)
        assert not any(d["code"] == "NO_IMPLICIT_NET" for d in diagnostics)

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
        assert not any(d["code"] == "NO_IMPLICIT_NET" for d in diagnostics)

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
        assert not any(d["code"] == "NO_IMPLICIT_NET" for d in diagnostics)

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

    def test_run_reports_class_declaration_rule(self) -> None:
        diagnostics = run([CLASS_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_CLASS_DECLARATION" for d in diagnostics)
        assert any("class declarations" in d["message"] for d in diagnostics)

    def test_run_reports_covergroup_declaration_rule(self) -> None:
        diagnostics = run([COVERGROUP_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_COVERGROUP_DECLARATION" for d in diagnostics)
        assert any("covergroup declarations" in d["message"] for d in diagnostics)

    def test_run_reports_sequence_declaration_rule(self) -> None:
        diagnostics = run([SEQUENCE_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_SEQUENCE_DECLARATION" for d in diagnostics)
        assert any("sequence declarations" in d["message"] for d in diagnostics)

    def test_run_reports_property_declaration_rule(self) -> None:
        diagnostics = run([PROPERTY_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_PROPERTY_DECLARATION" for d in diagnostics)
        assert any("property declarations" in d["message"] for d in diagnostics)

    def test_run_reports_function_declaration_rule(self) -> None:
        diagnostics = run([FUNCTION_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_FUNCTION_DECLARATION" for d in diagnostics)
        assert any("function declarations" in d["message"] for d in diagnostics)
        assert not any(
            d["code"] == "NO_IMPLICIT_NET" and "do_work" in d["message"] for d in diagnostics
        )

    def test_run_reports_uwire_rule(self) -> None:
        diagnostics = run([UWIRE_DATA], jobs=1)

        assert any(d["code"] == "NO_UWIRE" for d in diagnostics)
        assert any("uwire" in d["message"] for d in diagnostics)

    def test_run_reports_read_before_write_rule(self) -> None:
        diagnostics = run([READ_BEFORE_WRITE_DATA], jobs=1)

        assert any(d["code"] == "READ_BEFORE_WRITE" for d in diagnostics)
        assert any("read before write" in d["message"] for d in diagnostics)

    def test_run_reports_input_port_write_rule(self) -> None:
        diagnostics = run([INPUT_PORT_WRITE_DATA], jobs=1)

        assert any(d["code"] == "NO_INPUT_PORT_WRITE" for d in diagnostics)
        assert any("should not be written" in d["message"] for d in diagnostics)

    def test_run_reports_write_only_variable_rule(self) -> None:
        diagnostics = run([WRITE_ONLY_VARIABLE_DATA], jobs=1)

        assert any(d["code"] == "NO_WRITE_ONLY_VARIABLE" for d in diagnostics)
        assert any("written but never read" in d["message"] for d in diagnostics)

    def test_run_reports_mixed_assignment_style_rule(self) -> None:
        diagnostics = run([MIXED_ASSIGNMENT_STYLE_DATA], jobs=1)

        assert any(d["code"] == "NO_MIXED_ASSIGNMENT_STYLE" for d in diagnostics)
        assert any("Mixed blocking and non-blocking" in d["message"] for d in diagnostics)

    def test_run_reports_self_assignment_rule(self) -> None:
        diagnostics = run([SELF_ASSIGNMENT_DATA], jobs=1)

        assert any(d["code"] == "NO_SELF_ASSIGNMENT" for d in diagnostics)
        assert any("Self-assignment" in d["message"] for d in diagnostics)

    def test_run_reports_multiple_nonblocking_writes_rule(self) -> None:
        diagnostics = run([MULTIPLE_NONBLOCKING_WRITES_DATA], jobs=1)

        assert any(d["code"] == "NO_MULTIPLE_NONBLOCKING_WRITES" for d in diagnostics)
        assert any("Multiple non-blocking writes" in d["message"] for d in diagnostics)

    def test_run_reports_duplicate_case_item_rule(self) -> None:
        diagnostics = run([DUPLICATE_CASE_ITEM_DATA], jobs=1)

        assert any(d["code"] == "NO_DUPLICATE_CASE_ITEM" for d in diagnostics)
        assert any("Duplicate case item" in d["message"] for d in diagnostics)

    def test_run_reports_unconnected_instance_ports_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ISSUES_DATA], jobs=1)

        assert any(d["code"] == "NO_UNCONNECTED_INSTANCE_PORTS" for d in diagnostics)
        assert any("u_unconn" in d["message"] and "y" in d["message"] for d in diagnostics)

    def test_run_reports_let_declaration_rule(self) -> None:
        diagnostics = run([LET_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_LET_DECLARATION" for d in diagnostics)
        assert any("let declarations" in d["message"] for d in diagnostics)

    def test_run_reports_config_declaration_rule(self) -> None:
        diagnostics = run([CONFIG_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_CONFIG_DECLARATION" for d in diagnostics)
        assert any("config declarations" in d["message"] for d in diagnostics)

    def test_run_reports_randsequence_rule(self) -> None:
        diagnostics = run([RANDSEQUENCE_DATA], jobs=1)

        assert any(d["code"] == "NO_RANDSEQUENCE" for d in diagnostics)
        assert any("randsequence" in d["message"] for d in diagnostics)

    def test_run_reports_expect_restrict_property_rule(self) -> None:
        diagnostics = run([EXPECT_RESTRICT_PROPERTY_DATA], jobs=1)

        assert any(d["code"] == "NO_EXPECT_RESTRICT_PROPERTY" for d in diagnostics)
        assert any("expect/restrict property" in d["message"] for d in diagnostics)

    def test_run_reports_virtual_interface_rule(self) -> None:
        diagnostics = run([VIRTUAL_INTERFACE_DATA], jobs=1)

        assert any(d["code"] == "NO_VIRTUAL_INTERFACE" for d in diagnostics)
        assert any("virtual interface" in d["message"] for d in diagnostics)

    def test_run_reports_dpi_import_export_rule(self) -> None:
        diagnostics = run([DPI_IMPORT_EXPORT_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_DPI_IMPORT_EXPORT") == 2
        assert any("DPI import/export" in d["message"] for d in diagnostics)

    def test_run_reports_real_type_rule(self) -> None:
        diagnostics = run([REAL_TYPE_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_REAL_TYPE") == 3
        assert any("real/shortreal/realtime" in d["message"] for d in diagnostics)

    def test_run_reports_string_type_rule(self) -> None:
        diagnostics = run([STRING_TYPE_DATA], jobs=1)

        assert any(d["code"] == "NO_STRING_TYPE" for d in diagnostics)
        assert any("string type" in d["message"] for d in diagnostics)

    def test_run_reports_chandle_type_rule(self) -> None:
        diagnostics = run([CHANDLE_TYPE_DATA], jobs=1)

        assert any(d["code"] == "NO_CHANDLE_TYPE" for d in diagnostics)
        assert any("chandle type" in d["message"] for d in diagnostics)

    def test_run_reports_random_system_function_rule(self) -> None:
        diagnostics = run([RANDOM_SYSTEM_FUNCTION_DATA], jobs=1)

        assert any(d["code"] == "NO_RANDOM_SYSTEM_FUNCTION" for d in diagnostics)
        assert any("$random" in d["message"] for d in diagnostics)

    def test_run_reports_time_system_function_rule(self) -> None:
        diagnostics = run([TIME_SYSTEM_FUNCTION_DATA], jobs=1)

        assert any(d["code"] == "NO_TIME_SYSTEM_FUNCTION" for d in diagnostics)
        assert any("$time" in d["message"] for d in diagnostics)

    def test_run_reports_nonblocking_combinational_rule_for_plain_always_star(self) -> None:
        diagnostics = run([NONBLOCKING_COMBINATIONAL_DATA], jobs=1)

        assert any(d["code"] == "NO_NONBLOCKING_COMBINATIONAL" for d in diagnostics)

    def test_run_does_not_report_blocking_sequential_for_plain_always_star(self) -> None:
        """Regression test for the NO_BLOCKING_SEQUENTIAL false positive: a plain
        `always @(*)` block using the correct combinational `=` style must not be
        flagged as sequential logic."""
        diagnostics = run([BLOCKING_COMBINATIONAL_OK_DATA], jobs=1)

        assert not any(d["code"] == "NO_BLOCKING_SEQUENTIAL" for d in diagnostics)

    def test_run_reports_vcd_dump_task_rule(self) -> None:
        diagnostics = run([VCD_DUMP_TASK_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_VCD_DUMP_TASK") == 2
        assert any("VCD dump" in d["message"] for d in diagnostics)

    def test_run_reports_file_io_system_task_rule(self) -> None:
        diagnostics = run([FILE_IO_SYSTEM_TASK_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_FILE_IO_SYSTEM_TASK") == 3
        assert any("file I/O" in d["message"] for d in diagnostics)

    def test_run_reports_plusargs_system_function_rule(self) -> None:
        diagnostics = run([PLUSARGS_SYSTEM_FUNCTION_DATA], jobs=1)

        assert any(d["code"] == "NO_PLUSARGS_SYSTEM_FUNCTION" for d in diagnostics)
        assert any("plusargs" in d["message"] for d in diagnostics)

    def test_run_reports_assertion_control_task_rule(self) -> None:
        diagnostics = run([ASSERTION_CONTROL_TASK_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_ASSERTION_CONTROL_TASK") == 2
        assert any("assertion-control" in d["message"] for d in diagnostics)

    def test_run_reports_queue_rule(self) -> None:
        diagnostics = run([QUEUE_DATA], jobs=1)

        assert any(d["code"] == "NO_QUEUE" for d in diagnostics)
        assert any("queue" in d["message"].lower() for d in diagnostics)

    def test_run_reports_dynamic_array_rule(self) -> None:
        diagnostics = run([DYNAMIC_ARRAY_DATA], jobs=1)

        assert any(d["code"] == "NO_DYNAMIC_ARRAY" for d in diagnostics)
        assert any("dynamic array" in d["message"] for d in diagnostics)

    def test_run_reports_associative_array_rule(self) -> None:
        diagnostics = run([ASSOCIATIVE_ARRAY_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_ASSOCIATIVE_ARRAY") == 2
        assert any("associative array" in d["message"] for d in diagnostics)

    def test_run_reports_unique0_if_rule(self) -> None:
        diagnostics = run([UNIQUE0_IF_DATA], jobs=1)

        assert any(d["code"] == "NO_UNIQUE0_IF" for d in diagnostics)
        assert any("unique0 if" in d["message"] for d in diagnostics)

    def test_run_reports_switch_primitive_rule(self) -> None:
        diagnostics = run([SWITCH_PRIMITIVE_DATA], jobs=1)

        assert any(d["code"] == "NO_SWITCH_PRIMITIVE" for d in diagnostics)
        assert any("switch-level primitives" in d["message"] for d in diagnostics)

    def test_run_reports_unused_parameter_rule(self) -> None:
        diagnostics = run([UNUSED_PARAMETER_DATA], jobs=1)

        assert any(d["code"] == "NO_UNUSED_PARAMETER" for d in diagnostics)
        assert any("UNUSED_WIDTH" in d["message"] for d in diagnostics)
        assert not any(d["code"] == "NO_WRITE_ONLY_VARIABLE" for d in diagnostics)

    def test_run_reports_duplicate_named_port_connection_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ISSUES_DATA], jobs=1)

        assert any(d["code"] == "NO_DUPLICATE_NAMED_PORT_CONNECTION" for d in diagnostics)
        assert any("u_dup" in d["message"] and "data" in d["message"] for d in diagnostics)

    def test_run_reports_mixed_port_connection_style_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ISSUES_DATA], jobs=1)

        assert any(d["code"] == "NO_MIXED_PORT_CONNECTION_STYLE" for d in diagnostics)
        assert any("u_mixed" in d["message"] for d in diagnostics)

    def test_run_reports_port_connection_width_mismatch_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ISSUES_DATA], jobs=1)

        assert any(d["code"] == "PORT_CONNECTION_WIDTH_MISMATCH" for d in diagnostics)
        assert any("u_width" in d["message"] and "width 8" in d["message"] for d in diagnostics)

    def test_run_reports_port_connection_signedness_mismatch_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ISSUES_DATA], jobs=1)

        assert any(d["code"] == "PORT_CONNECTION_SIGNEDNESS_MISMATCH" for d in diagnostics)
        assert any("u_width" in d["message"] and "unsigned" in d["message"] for d in diagnostics)

    def test_run_reports_slice_and_replication_width_mismatches(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        mismatches = [d for d in diagnostics if d["code"] == "PORT_CONNECTION_WIDTH_MISMATCH"]
        assert any("u_slice_mismatch" in d["message"] and "bus8[5:0]" in d["message"] for d in mismatches)
        assert any("u_rep_mismatch" in d["message"] and "{3{pair}}" in d["message"] for d in mismatches)

    def test_run_reports_unknown_named_port_connection_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        assert any(d["code"] == "UNKNOWN_NAMED_PORT_CONNECTION" for d in diagnostics)
        assert any("u_bad_port" in d["message"] and "qq" in d["message"] for d in diagnostics)

    def test_run_reports_width_unknown_when_inference_is_not_confident(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        assert any(d["code"] == "PORT_CONNECTION_WIDTH_UNKNOWN" for d in diagnostics)
        assert any("u_rep_mismatch" in d["message"] and "Cannot infer width confidently" in d["message"] for d in diagnostics)
        assert any("u_unknown" in d["message"] and "unknown port width" in d["message"] for d in diagnostics)

    def test_run_reports_unread_instance_output_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        assert any(d["code"] == "UNREAD_INSTANCE_OUTPUT" for d in diagnostics)
        assert any("u_slice_mismatch" in d["message"] and "out_unused" in d["message"] for d in diagnostics)

    def test_run_reports_extra_ordered_port_connection_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        assert any(d["code"] == "EXTRA_ORDERED_PORT_CONNECTION" for d in diagnostics)

    def test_run_reports_unknown_named_parameter_override_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        assert any(
            d["code"] == "UNKNOWN_NAMED_PARAMETER_OVERRIDE" and "BOGUS_PARAM" in d["message"]
            for d in diagnostics
        )

    def test_run_reports_duplicate_named_parameter_override_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        assert any(d["code"] == "NO_DUPLICATE_NAMED_PARAMETER_OVERRIDE" for d in diagnostics)

    def test_run_reports_mixed_parameter_override_style_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        assert any(d["code"] == "NO_MIXED_PARAMETER_OVERRIDE_STYLE" for d in diagnostics)

    def test_run_reports_ordered_port_connections_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        assert any(d["code"] == "NO_ORDERED_PORT_CONNECTIONS" for d in diagnostics)
        assert any("u_extra_ordered" in d["message"] for d in diagnostics)

    def test_run_reports_ordered_parameter_overrides_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        assert any(d["code"] == "NO_ORDERED_PARAMETER_OVERRIDES" for d in diagnostics)
        assert any("u_mixed_param_override" in d["message"] for d in diagnostics)

    def test_run_reports_wildcard_port_connection_rule(self) -> None:
        diagnostics = run([WILDCARD_PORT_CONNECTION_DATA], jobs=1)

        assert any(d["code"] == "NO_WILDCARD_PORT_CONNECTION" for d in diagnostics)
        assert any("u_wild" in d["message"] and "(.*)" in d["message"] for d in diagnostics)

    def test_run_does_not_pile_on_explicit_port_mapping_checks_for_wildcard_connections(self) -> None:
        diagnostics = run([WILDCARD_PORT_CONNECTION_DATA], jobs=1)

        blocked_codes = {
            "NO_UNCONNECTED_INSTANCE_PORTS",
            "PORT_CONNECTION_WIDTH_MISMATCH",
            "PORT_CONNECTION_WIDTH_UNKNOWN",
            "PORT_CONNECTION_SIGNEDNESS_MISMATCH",
            "UNREAD_INSTANCE_OUTPUT",
        }
        assert not any(d["code"] in blocked_codes for d in diagnostics)

    def test_run_does_not_double_report_unknown_parameter_override_for_undefined_module(self) -> None:
        """Regression test: when the instantiated module type is undefined, that's
        already `UNDEFINED_MODULE`'s concern -- `UNKNOWN_NAMED_PARAMETER_OVERRIDE`
        (and the equivalent port-connection check) must not pile on a misleading
        'unknown parameter/port' diagnostic per connection on top of it, since there
        is no real parameter/port list to check against in the first place."""
        diagnostics = run([UNDEFINED_MODULE_PARAM_OVERRIDE_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("UNDEFINED_MODULE") == 1
        assert "UNKNOWN_NAMED_PARAMETER_OVERRIDE" not in codes
        assert "UNKNOWN_NAMED_PORT_CONNECTION" not in codes

    def test_run_does_not_flag_named_type_reference_as_implicit_net(self) -> None:
        diagnostics = run([NAMED_TYPE_REFERENCE_DATA], jobs=1)

        assert not any(d["code"] == "NO_IMPLICIT_NET" for d in diagnostics)

    def test_run_does_not_flag_invocation_callee_as_implicit_net(self) -> None:
        diagnostics = run([INVOCATION_CALLEE_DATA], jobs=1)

        assert not any(d["code"] == "NO_IMPLICIT_NET" for d in diagnostics)

    def test_run_does_not_flag_cover_cross_items_as_implicit_net(self) -> None:
        diagnostics = run([COVER_CROSS_DATA], jobs=1)

        assert any(d["code"] == "NO_COVERGROUP_DECLARATION" for d in diagnostics)
        assert not any(d["code"] == "NO_IMPLICIT_NET" for d in diagnostics)

    def test_run_does_not_flag_extends_clause_base_name_as_implicit_net(self) -> None:
        diagnostics = run([EXTENDS_CLAUSE_DATA], jobs=1)

        assert any(d["code"] == "NO_CLASS_DECLARATION" for d in diagnostics)
        assert not any(d["code"] == "NO_IMPLICIT_NET" for d in diagnostics)

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

    def test_run_aggregates_multi_file_diagnostics_after_per_file_workers(
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
        assert sorted(d["code"] for d in diagnostics) == [
            "AST_FAKE",
            "AST_FAKE",
            "MODULE_FAKE",
            "SYMBOL_FAKE",
            "SYMBOL_FAKE",
        ]
        assert sum(1 for d in diagnostics if d["file"] == str(first)) == 2
        assert sum(1 for d in diagnostics if d["file"] == str(second)) == 3

    def test_run_reports_unsized_literal_rule(self) -> None:
        diagnostics = run([UNSIZED_LITERAL_DATA], jobs=1)

        assert any(d["code"] == "NO_UNSIZED_LITERAL" for d in diagnostics)

    def test_run_reports_if_without_begin_end_rule(self) -> None:
        diagnostics = run([IF_WITHOUT_BEGIN_END_DATA], jobs=1)

        assert any(d["code"] == "NO_IF_WITHOUT_BEGIN_END" for d in diagnostics)
        assert any(d["code"] == "NO_ELSE_WITHOUT_BEGIN_END" for d in diagnostics)

    def test_run_reports_missing_timescale_directive_rule(self) -> None:
        diagnostics = run([MISSING_TIMESCALE_DIRECTIVE_DATA], jobs=1)

        assert any(d["code"] == "MISSING_TIMESCALE_DIRECTIVE" for d in diagnostics)

    def test_run_does_not_report_missing_timescale_directive_when_present(self) -> None:
        diagnostics = run([HAS_TIMESCALE_DIRECTIVE_DATA], jobs=1)

        assert not any(d["code"] == "MISSING_TIMESCALE_DIRECTIVE" for d in diagnostics)


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
        monkeypatch.setattr(
            "src.run_lint.analyze",
            lambda paths, jobs=1, **kwargs: type("A", (), {"diagnostics": [], "symbol_table": object()})(),
        )

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
            "src.run_lint.analyze",
            lambda paths, jobs=1, **kwargs: type(
                "A",
                (),
                {
                    "diagnostics": [
                        {
                            "code": "UNUSED_VARIABLE",
                            "line": 3,
                            "col": 7,
                            "message": "Example diagnostic",
                            "file": "demo.sv",
                            "severity": "warning",
                        }
                    ],
                    "symbol_table": object(),
                },
            )(),
        )

        result = main([str(DATA)])

        captured = capsys.readouterr()
        assert result == 0
        assert "demo.sv:3:7" in captured.out
        assert "Example diagnostic" in captured.out
        assert "[UNUSED_VARIABLE]" in captured.out
        assert "[WARNING]" in captured.out

    def test_main_prints_multiple_diagnostics(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "src.run_lint.analyze",
            lambda paths, jobs=1, **kwargs: type(
                "A",
                (),
                {
                    "diagnostics": [
                        {
                            "code": "FIRST",
                            "line": 3,
                            "col": 7,
                            "message": "First diagnostic",
                            "file": "demo_a.sv",
                            "severity": "warning",
                        },
                        {
                            "code": "SECOND",
                            "line": 8,
                            "col": 2,
                            "message": "Second diagnostic",
                            "file": "demo_b.sv",
                            "severity": "error",
                        },
                    ],
                    "symbol_table": object(),
                },
            )(),
        )

        result = main([str(DATA)])

        captured = capsys.readouterr()
        assert result == 0
        assert "demo_a.sv:3:7 - [FIRST] [WARNING] First diagnostic" in captured.out
        assert "demo_b.sv:8:2 - [SECOND] [ERROR] Second diagnostic" in captured.out


class TestRunRuleSelection:
    def test_run_resolves_named_rule_profile(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
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
            seen["selection"] = passed_selection
            return []

        monkeypatch.setattr(run_lint_module, "parse_file", fake_parse_file)
        monkeypatch.setattr(run_lint_module, "file_uses_default_nettype_none", lambda path: False)
        monkeypatch.setattr(run_lint_module, "Walker", FakeWalker)
        monkeypatch.setattr(run_lint_module.rule_runner, "check", fake_rule_check)
        monkeypatch.setattr(run_lint_module.symbol_rule_runner, "run", lambda symbol_table, passed_selection=None: [])
        monkeypatch.setattr(run_lint_module.module_rule_runner, "run", lambda symbol_table, passed_selection=None: [])

        diagnostics = run([DATA], jobs=1, rule_profile="sv_rtl_subset")

        assert diagnostics == []
        selection = seen["selection"]
        assert selection is not None
        assert getattr(selection, "enabled_codes") is None
        assert getattr(selection, "enabled_categories") is None
        assert getattr(selection, "enabled_profiles") == frozenset({"sv_rtl_subset"})

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
