"""Harness for "this must return, and not take pathologically long" checks.

The stress and traversal-safety tests feed cyclic or deeply nested input to
code that must stop. A genuine non-termination bug shows up as a hang or a
`RecursionError`, both of which are already distinct failures. What a time
budget adds is a guard against runaway slowness, which is also what a busy
machine looks like. This module keeps that check in one place so that:

* the budget is one named constant, scaled by `VERILINTER_TEST_TIME_SCALE`
  (set it to 3 or 5 on a loaded machine or slow CI runner);
* a budget failure says it is a slowness failure, names the test and the
  budget, and says how to tell load from a real regression;
* an exception raised inside the block propagates untouched, so a real
  `RecursionError` is never reported as a timing problem.
"""
from __future__ import annotations

import os
import time
from collections.abc import Iterator
from contextlib import contextmanager

# Ceiling for "returned promptly" on the small synthetic inputs used in
# stress tests. Well above their normal cost (well under 0.1s) and far below
# what a runaway traversal costs, so it catches blow-ups and ignores noise.
DEFAULT_BUDGET_S = 1.0

TIME_SCALE_ENV = "VERILINTER_TEST_TIME_SCALE"


class TerminationBudgetExceeded(AssertionError):
    """The block returned, but slower than its budget allows."""


def time_scale() -> float:
    raw = os.environ.get(TIME_SCALE_ENV, "1")
    try:
        scale = float(raw)
    except ValueError:
        raise ValueError(f"{TIME_SCALE_ENV} must be a number, got {raw!r}") from None
    if scale <= 0:
        raise ValueError(f"{TIME_SCALE_ENV} must be positive, got {raw!r}")
    return scale


def _current_test_label() -> str:
    current = os.environ.get("PYTEST_CURRENT_TEST", "")
    # "path::test_name[param] (call)" -> "path::test_name[param]"
    return current.rsplit(" ", 1)[0] if current else "<unlabelled>"


@contextmanager
def terminates_within(label: str | None = None, *, budget_s: float = DEFAULT_BUDGET_S) -> Iterator[None]:
    """Fail if the block takes longer than `budget_s` x `time_scale()` seconds.

    `label` defaults to the running test's id, including its parameters.
    """
    limit = budget_s * time_scale()
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    if elapsed > limit:
        raise TerminationBudgetExceeded(
            f"[termination budget] {label or _current_test_label()}: returned after "
            f"{elapsed:.3f}s, budget {limit:.3f}s ({budget_s}s x {TIME_SCALE_ENV}={time_scale():g}).\n"
            "It terminated, so this is slowness and not an infinite loop or unbounded "
            "recursion (those hang or raise RecursionError).\n"
            "Rerun this test alone: if it passes, the machine was loaded (raise "
            f"{TIME_SCALE_ENV}); if it fails alone, look for a real slowdown."
        )


__all__ = [
    "DEFAULT_BUDGET_S",
    "TIME_SCALE_ENV",
    "TerminationBudgetExceeded",
    "terminates_within",
    "time_scale",
]
