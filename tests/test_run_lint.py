from pathlib import Path

import pytest

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
