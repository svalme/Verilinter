"""`run` reports the procedural statement, loop, declaration and case rules."""
from pathlib import Path
from src.run_lint import run
from tests.support.run_lint_helpers import INITIAL_BLOCK_DATA


FINAL_BLOCK_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "final_block.v"


ALWAYS_FF_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "always_ff.v"


ALWAYS_LATCH_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "always_latch.v"


FOREVER_LOOP_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "forever_loop.v"


REPEAT_LOOP_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "repeat_loop.v"


WAIT_STATEMENT_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "wait_statement.v"


WHILE_LOOP_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "while_loop.v"


FOREACH_LOOP_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "foreach_loop.v"


DO_WHILE_LOOP_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "do_while_loop.v"


FOR_LOOP_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "for_loop.v"


GENERATE_FOR_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "generate_for.v"


IF_GENERATE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "if_generate.v"


GENERATE_BLOCK_MISSING_LABEL_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "generate_block_missing_label.v"


TASK_DECLARATION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "task_declaration.v"


PROGRAM_DECLARATION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "program_declaration.sv"


CLOCKING_DECLARATION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "clocking_declaration.sv"


CHECKER_DECLARATION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "checker_declaration.sv"


INTERFACE_DECLARATION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "interface_declaration.sv"


MODPORT_DECLARATION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "modport_declaration.sv"


PACKAGE_DECLARATION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "package_declaration.sv"


DISABLE_STATEMENT_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "disable_statement.v"


EVENT_TRIGGER_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "event_trigger.v"


FORK_JOIN_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "fork_join.v"


CASE_GENERATE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "case_generate.v"


CASE_INSIDE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "case_inside.v"


FULL_PARALLEL_CASE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "full_parallel_case.v"


INSIDE_OPERATOR_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "inside_operator.v"


UNIQUE_PRIORITY_CASE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "unique_priority_case.v"


UNIQUE0_CASE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "unique0_case.v"


UNIQUE_IF_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "unique_if.v"


PRIORITY_IF_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "priority_if.v"


class TestRunReportsStatementRules:
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
