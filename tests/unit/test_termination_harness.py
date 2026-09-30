from __future__ import annotations

import time

import pytest

from tests.support.termination import (
    TIME_SCALE_ENV,
    TerminationBudgetExceeded,
    terminates_within,
    time_scale,
)


def test_fast_block_passes() -> None:
    with terminates_within(budget_s=1.0):
        pass


def test_slow_block_reports_slowness_with_guidance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(TIME_SCALE_ENV, raising=False)
    with pytest.raises(TerminationBudgetExceeded) as info:
        with terminates_within("my query", budget_s=0.01):
            time.sleep(0.05)
    message = str(info.value)
    assert "my query" in message
    assert "budget 0.010s" in message
    assert "slowness and not an infinite loop" in message
    assert TIME_SCALE_ENV in message


def test_time_scale_widens_the_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(TIME_SCALE_ENV, "100")
    with terminates_within(budget_s=0.01):
        time.sleep(0.05)


def test_default_label_is_the_running_test_id() -> None:
    with pytest.raises(TerminationBudgetExceeded, match="test_default_label_is_the_running_test_id"):
        with terminates_within(budget_s=0.0):
            time.sleep(0.01)


def test_exception_inside_block_is_not_reported_as_timing() -> None:
    with pytest.raises(RecursionError):
        with terminates_within(budget_s=0.0):
            raise RecursionError("real bug")


@pytest.mark.parametrize("bad", ["abc", "0", "-2"])
def test_invalid_time_scale_is_rejected(monkeypatch: pytest.MonkeyPatch, bad: str) -> None:
    monkeypatch.setenv(TIME_SCALE_ENV, bad)
    with pytest.raises(ValueError, match=TIME_SCALE_ENV):
        time_scale()
