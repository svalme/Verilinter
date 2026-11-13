from __future__ import annotations

import inspect

import pytest

from src.pkg.rules.rule_selection import RuleSelection
from src.pkg.store import keys
from src.pkg.store.keys import selection_key


def _base() -> str:
    return selection_key(None, ["inc"], "fingerprint", defines=["A=1"])


class TestKeyChangesWithEveryInput:
    def test_rule_selection_codes(self) -> None:
        selection = RuleSelection(enabled_codes={"NO_LATCH"})
        assert selection_key(selection, ["inc"], "fingerprint", defines=["A=1"]) != _base()

    def test_include_directories_and_their_order(self) -> None:
        assert selection_key(None, ["other"], "fingerprint", defines=["A=1"]) != _base()
        assert selection_key(None, ["a", "b"]) != selection_key(None, ["b", "a"])

    def test_defines(self) -> None:
        assert selection_key(None, ["inc"], "fingerprint", defines=["A=2"]) != _base()

    def test_cross_file_fingerprint(self) -> None:
        assert selection_key(None, ["inc"], "changed", defines=["A=1"]) != _base()

    def test_analyzer_cache_version(self, monkeypatch: pytest.MonkeyPatch) -> None:
        before = _base()
        monkeypatch.setattr(keys, "ANALYZER_CACHE_VERSION", "bumped-for-test")
        assert _base() != before

    def test_pyslang_version(self, monkeypatch: pytest.MonkeyPatch) -> None:
        before = _base()
        monkeypatch.setattr(keys, "pyslang_version", lambda: "0.0.0-test")
        assert _base() != before

    def test_analyzer_source(self, monkeypatch: pytest.MonkeyPatch) -> None:
        before = _base()
        monkeypatch.setattr(keys, "analyzer_code_fingerprint", lambda: "edited-source")
        assert _base() != before


class TestKeyIgnoresWhatDoesNotChangeResults:
    def test_key_takes_no_severity_or_job_input(self) -> None:
        # Severity overrides are applied after cached results load and `--jobs` only changes scheduling, so the
        # key function must not grow a parameter for either.
        assert set(inspect.signature(selection_key).parameters) == {
            "selection",
            "include_dirs",
            "package_registry_fingerprint",
            "defines",
        }

    def test_same_inputs_give_the_same_key(self) -> None:
        assert _base() == _base()

    def test_define_order_does_not_matter(self) -> None:
        assert selection_key(None, None, None, defines=["A", "B"]) == selection_key(None, None, None, defines=["B", "A"])


class TestCodeFingerprint:
    def test_is_stable_within_a_process(self) -> None:
        assert keys.analyzer_code_fingerprint() == keys.analyzer_code_fingerprint()
        assert len(keys.analyzer_code_fingerprint()) == 16

    def test_pyslang_version_is_reported(self) -> None:
        assert keys.pyslang_version() not in {"", "unknown"}
