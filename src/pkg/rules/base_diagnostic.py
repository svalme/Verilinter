from abc import ABC
from typing import Any

from ..vnodes.base_vnode import BaseVNode


class BaseDiagnostic(ABC):
    code: str = "UNSPEC"
    message: str = "No message"
    category: str = "uncategorized"
    default_profiles: tuple[str, ...] = ()
    # Purely declarative cross-reference: other rule codes that can plausibly
    # co-fire with (or need to be suppressed relative to) this one on the same
    # symbol/construct. Has no runtime effect -- runners still just concatenate
    # every rule's diagnostics (see symbol_rule_runner.py). Its only purpose is
    # to be machine-checked against tests/test_rule_overlap_harness.py so a
    # known overlap can never silently lose its regression test; see
    # tests/test_rule_overlap_metadata.py and docs/RULE_IMPLEMENTATION.md.
    overlaps_with: tuple[str, ...] = ()

    def report(self, vnode: BaseVNode) -> dict[str, Any]:
        loc = vnode.location or {}
        diagnostic: dict[str, Any] = {
            "code": self.code,
            "line": loc.get("line", 0),
            "col": loc.get("col", 0),
            "message": self.message,
        }
        if "file" in loc:
            diagnostic["file"] = loc["file"]
        return diagnostic
