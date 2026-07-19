from pathlib import Path

import pytest

import src.run_lint as run_lint_module
from src.run_lint import main, run

DATA = Path(__file__).parent / "data" / "simple.v"
INITIAL_BLOCK_DATA = Path(__file__).parent / "data" / "initial_block.v"
FINAL_BLOCK_DATA = Path(__file__).parent / "data" / "final_block.v"
ALWAYS_LATCH_DATA = Path(__file__).parent / "data" / "always_latch.v"
CASE_GENERATE_DATA = Path(__file__).parent / "data" / "case_generate.v"
FULL_PARALLEL_CASE_DATA = Path(__file__).parent / "data" / "full_parallel_case.v"
UNIQUE_PRIORITY_CASE_DATA = Path(__file__).parent / "data" / "unique_priority_case.v"


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

    def test_run_reports_case_generate_rule(self) -> None:
        diagnostics = run([CASE_GENERATE_DATA], jobs=1)

        assert any(d["code"] == "NO_CASE_GENERATE" for d in diagnostics)
        assert any("case generate" in d["message"] for d in diagnostics)

    def test_run_reports_unique_priority_case_rule(self) -> None:
        diagnostics = run([UNIQUE_PRIORITY_CASE_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_UNIQUE_PRIORITY_CASE") == 2
        assert any("unique/priority case" in d["message"] for d in diagnostics)

    def test_run_reports_full_parallel_case_rule(self) -> None:
        diagnostics = run([FULL_PARALLEL_CASE_DATA], jobs=1)

        assert any(d["code"] == "NO_FULL_PARALLEL_CASE" for d in diagnostics)
        assert any("full_case / parallel_case" in d["message"] for d in diagnostics)

    def test_run_reports_no_implicit_net_rule(self) -> None:
        diagnostics = run([DATA], jobs=1)

        assert any(d["code"] == "NO_IMPLICIT_NET" for d in diagnostics)
        assert any("Implicit net" in d["message"] for d in diagnostics)

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
        monkeypatch.setattr(run_lint_module, "Walker", FakeWalker)
        monkeypatch.setattr(run_lint_module.symbol_rule_runner, "run", lambda symbol_table: [])
        monkeypatch.setattr(run_lint_module.module_rule_runner, "run", lambda symbol_table: [])

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

        def fake_rule_check(vnode: object, _ctx: object) -> list[dict[str, object]]:
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
        monkeypatch.setattr(run_lint_module, "Walker", FakeWalker)
        monkeypatch.setattr(run_lint_module.rule_runner, "check", fake_rule_check)
        monkeypatch.setattr(
            run_lint_module.symbol_rule_runner,
            "run",
            lambda symbol_table: [
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
            lambda _symbol_table: [
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
