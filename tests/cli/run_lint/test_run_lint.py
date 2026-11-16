"""`run`: jobs, input discovery, include directories, rule selection and `main`."""
from pathlib import Path
import pytest
import src.run_lint as run_lint_module
from src.pkg.parser.parse import parse_file
from src.pkg.rules.rule_selection import RuleSelection
from src.run_lint import collect_paths, main, run
from tests.support.run_lint_helpers import DATA


class TestRunJobsAndInputs:
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


class TestCollectPathsFileDiscovery:
    """Direct coverage of `collect_paths`'s three input shapes -- a whole
    directory (recursive), a single explicitly named file, and a mix of both
    -- including recursion into *nested* subdirectories, which the flat
    fixture directory (`tests/data`) cannot exercise."""

    def test_finds_files_at_multiple_nesting_depths(self, tmp_path: Path) -> None:
        (tmp_path / "top.v").write_text("module top; endmodule\n")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "mid.v").write_text("module mid; endmodule\n")
        deep = sub / "deep"
        deep.mkdir()
        (deep / "bottom.sv").write_text("module bottom; endmodule\n")

        paths = collect_paths([str(tmp_path)])

        names = {p.name for p in paths}
        assert names == {"top.v", "mid.v", "bottom.sv"}

    def test_ignores_non_verilog_files_when_a_directory_is_passed(self, tmp_path: Path) -> None:
        (tmp_path / "design.v").write_text("module design; endmodule\n")
        (tmp_path / "notes.txt").write_text("not RTL\n")
        (tmp_path / "README.md").write_text("# not RTL\n")

        paths = collect_paths([str(tmp_path)])

        assert [p.name for p in paths] == ["design.v"]

    def test_finds_both_v_and_sv_extensions(self, tmp_path: Path) -> None:
        (tmp_path / "legacy.v").write_text("module legacy; endmodule\n")
        (tmp_path / "modern.sv").write_text("module modern; endmodule\n")

        paths = collect_paths([str(tmp_path)])

        assert {p.name for p in paths} == {"legacy.v", "modern.sv"}

    def test_explicitly_named_file_is_included_regardless_of_extension(self, tmp_path: Path) -> None:
        """Documents current behavior, not a guarantee this is the ideal
        behavior: a *directory* argument is filtered to `.v`/`.sv`, but a
        file named directly on the command line is trusted as-is with no
        extension check at all -- `collect_paths` only special-cases
        directories (`p.is_dir()`), so `verilinter some_file.txt` would
        attempt to lint it."""
        odd_file = tmp_path / "design.inc"
        odd_file.write_text("module design; endmodule\n")

        paths = collect_paths([str(odd_file)])

        assert [p.name for p in paths] == ["design.inc"]

    def test_combines_directory_and_explicit_file_arguments(self, tmp_path: Path) -> None:
        dir_a = tmp_path / "a"
        dir_a.mkdir()
        (dir_a / "in_a.v").write_text("module in_a; endmodule\n")
        standalone = tmp_path / "standalone.v"
        standalone.write_text("module standalone; endmodule\n")

        paths = collect_paths([str(dir_a), str(standalone)])

        assert {p.name for p in paths} == {"in_a.v", "standalone.v"}

    def test_exclude_filters_by_filename_pattern_regardless_of_directory(self, tmp_path: Path) -> None:
        """A single-component pattern like `*_tb.v` matches from the right, so
        it excludes a testbench no matter which directory it's nested under, so
        testbenches can be skipped across a whole tree without enumerating
        every directory."""
        (tmp_path / "design.v").write_text("module design; endmodule\n")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "design_tb.v").write_text("module design_tb; endmodule\n")

        paths = collect_paths([str(tmp_path)], exclude=["*_tb.v"])

        assert [p.name for p in paths] == ["design.v"]

    def test_exclude_filters_by_directory_pattern(self, tmp_path: Path) -> None:
        (tmp_path / "design.v").write_text("module design; endmodule\n")
        vendor = tmp_path / "vendor"
        vendor.mkdir()
        (vendor / "cell.v").write_text("module cell; endmodule\n")

        paths = collect_paths([str(tmp_path)], exclude=["vendor/*"])

        assert [p.name for p in paths] == ["design.v"]

    def test_exclude_applies_to_explicitly_named_files_too(self, tmp_path: Path) -> None:
        excluded = tmp_path / "skip_tb.v"
        excluded.write_text("module skip_tb; endmodule\n")
        kept = tmp_path / "keep.v"
        kept.write_text("module keep; endmodule\n")

        paths = collect_paths([str(excluded), str(kept)], exclude=["*_tb.v"])

        assert [p.name for p in paths] == ["keep.v"]

    def test_no_exclude_patterns_behaves_exactly_as_before(self, tmp_path: Path) -> None:
        (tmp_path / "design.v").write_text("module design; endmodule\n")

        assert collect_paths([str(tmp_path)]) == collect_paths([str(tmp_path)], exclude=None)
        assert collect_paths([str(tmp_path)]) == collect_paths([str(tmp_path)], exclude=[])


class TestIncludeDirs:
    """`--include-dir`/`include_dirs` lets `` `include "..." `` resolve a
    header outside the source file's own directory -- pyslang's default
    `SourceManager` only looks there, so a vendored shared macro/assertion
    header (e.g. a shared assertion-macro header included by files elsewhere
    in the tree) fails with
    "unknown macro or compiler directive" for every subsequent use of a
    macro it defines, corrupting the rest of the file's parse."""

    HEADER_NAME = "shared_macros.svh"
    HEADER_CONTENT = "`define MY_WIDTH 8\n"
    SOURCE_TEMPLATE = (
        '`include "shared_macros.svh"\n'
        "module dut;\n"
        "  wire [`MY_WIDTH-1:0] data;\n"
        "endmodule\n"
    )

    def _write_fixture(self, tmp_path: Path) -> tuple[Path, Path]:
        headers_dir = tmp_path / "headers"
        headers_dir.mkdir()
        (headers_dir / self.HEADER_NAME).write_text(self.HEADER_CONTENT)
        source = tmp_path / "design.sv"
        source.write_text(self.SOURCE_TEMPLATE)
        return source, headers_dir

    def test_parse_file_resolves_include_from_extra_directory(self, tmp_path: Path) -> None:
        source, headers_dir = self._write_fixture(tmp_path)

        tree = parse_file(str(source), include_dirs=[str(headers_dir)])

        assert [d for d in tree.diagnostics if d.isError()] == []

    def test_parse_file_without_include_dirs_leaves_real_errors(self, tmp_path: Path) -> None:
        """Confirms the failure mode this feature closes: without the search
        directory, the macro is genuinely unresolved -- not a hypothetical."""
        source, _headers_dir = self._write_fixture(tmp_path)

        tree = parse_file(str(source))

        assert [d for d in tree.diagnostics if d.isError()] != []

    def test_run_threads_include_dirs_to_parse_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        received: list[list[str] | None] = []

        class FakeTree:
            def __init__(self) -> None:
                self.root = object()

        def fake_parse_file(path: str, include_dirs=None) -> FakeTree:
            received.append(include_dirs)
            return FakeTree()

        class FakeWalker:
            def __init__(self, dispatch: object) -> None:
                pass

            def walk(self, root, tree, ctx, symbol_table, on_node=None) -> None:
                pass

        monkeypatch.setattr(run_lint_module, "parse_file", fake_parse_file)
        monkeypatch.setattr(run_lint_module, "Walker", FakeWalker)

        run([DATA], include_dirs=["/some/vendored/headers"])

        assert received == [["/some/vendored/headers"]] * 2


class TestMain:
    def test_main_returns_zero_for_valid_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = main([str(DATA)])

        captured = capsys.readouterr()
        assert result == 0
        assert captured.err.startswith("Verilinter ")
        assert "Verilinter" not in captured.out

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

        def fake_parse_file(path: str, include_dirs=None) -> FakeTree:
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

        def fake_parse_file(path: str, include_dirs=None) -> FakeTree:
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
