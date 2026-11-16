"""`run` reports the signal, assignment, literal and file-level rules."""
from pathlib import Path
import pytest
import src.run_lint as run_lint_module
from src.pkg.parser.parse import parse_file
from src.pkg.rules.rule_selection import RuleSelection
from src.run_lint import run
from tests.support.run_lint_helpers import DATA, INITIAL_BLOCK_DATA


MULTIPLE_DRIVERS_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "multiple_drivers.v"


INTERNAL_INOUT_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "internal_inout.v"


UNDRIVEN_SIGNAL_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "undriven_signal.v"


DEFAULT_NETTYPE_NONE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "default_nettype_none.v"


LATCH_IN_ALWAYS_COMB_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "latch_in_always_comb.v"


READ_BEFORE_WRITE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "read_before_write.v"


INPUT_PORT_WRITE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "input_port_write.v"


WRITE_ONLY_VARIABLE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "write_only_variable.v"


MIXED_ASSIGNMENT_STYLE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "mixed_assignment_style.v"


NAMED_TYPE_REFERENCE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "named_type_reference.sv"


INVOCATION_CALLEE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "invocation_callee.sv"


COVER_CROSS_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "cover_cross.sv"


EXTENDS_CLAUSE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "extends_clause.sv"


SELF_ASSIGNMENT_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "self_assignment.v"


MULTIPLE_NONBLOCKING_WRITES_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "multiple_nonblocking_writes.v"


DUPLICATE_CASE_ITEM_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "duplicate_case_item.v"


NONBLOCKING_COMBINATIONAL_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "nonblocking_combinational.v"


BLOCKING_COMBINATIONAL_OK_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "blocking_combinational_ok.v"


UNUSED_PARAMETER_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "unused_parameter.v"


UNSIZED_LITERAL_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "unsized_literal.v"


IF_WITHOUT_BEGIN_END_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "if_without_begin_end.v"


MISSING_TIMESCALE_DIRECTIVE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "missing_timescale_directive.v"


HAS_TIMESCALE_DIRECTIVE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "has_timescale_directive.v"


ONE_MODULE_PER_FILE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "one_module_per_file.v"


MODULE_FILENAME_MISMATCH_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "module_filename_mismatch.v"


MODULE_FILENAME_MATCH_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "module_filename_match.v"


class TestRunReportsSignalAndFileRules:
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

    def test_run_reports_nonblocking_combinational_rule_for_plain_always_star(self) -> None:
        diagnostics = run([NONBLOCKING_COMBINATIONAL_DATA], jobs=1)

        assert any(d["code"] == "NO_NONBLOCKING_COMBINATIONAL" for d in diagnostics)

    def test_run_does_not_report_blocking_sequential_for_plain_always_star(self) -> None:
        """Regression test for the NO_BLOCKING_SEQUENTIAL false positive: a plain
        `always @(*)` block using the correct combinational `=` style must not be
        flagged as sequential logic."""
        diagnostics = run([BLOCKING_COMBINATIONAL_OK_DATA], jobs=1)

        assert not any(d["code"] == "NO_BLOCKING_SEQUENTIAL" for d in diagnostics)

    def test_run_reports_unused_parameter_rule(self) -> None:
        diagnostics = run([UNUSED_PARAMETER_DATA], jobs=1)

        assert any(d["code"] == "NO_UNUSED_PARAMETER" for d in diagnostics)
        assert any("SPARE_WIDTH" in d["message"] for d in diagnostics)
        assert not any(d["code"] == "NO_WRITE_ONLY_VARIABLE" for d in diagnostics)

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

        def fake_parse_file(path: str, include_dirs=None) -> FakeTree:
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
        # Each file is parsed once to record its module ports, then once for its own lint.
        assert parse_calls == [str(first), str(second), str(first), str(second)]
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

        def fake_parse_file(path: str, include_dirs=None) -> FakeTree:
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

        assert parse_calls == [str(first), str(second), str(first), str(second)]
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

    def test_run_reports_one_module_per_file_rule(self) -> None:
        diagnostics = run([ONE_MODULE_PER_FILE_DATA], jobs=1)

        assert sum(1 for d in diagnostics if d["code"] == "ONE_MODULE_PER_FILE") == 1

    def test_run_does_not_report_one_module_per_file_for_single_module_file(self) -> None:
        diagnostics = run([DATA], jobs=1)

        assert not any(d["code"] == "ONE_MODULE_PER_FILE" for d in diagnostics)

    def test_run_reports_module_filename_mismatch_rule(self) -> None:
        diagnostics = run([MODULE_FILENAME_MISMATCH_DATA], jobs=1)

        assert any(d["code"] == "MODULE_FILENAME_MISMATCH" for d in diagnostics)

    def test_run_does_not_report_module_filename_mismatch_when_names_match(self) -> None:
        diagnostics = run([MODULE_FILENAME_MATCH_DATA], jobs=1)

        assert not any(d["code"] == "MODULE_FILENAME_MISMATCH" for d in diagnostics)
