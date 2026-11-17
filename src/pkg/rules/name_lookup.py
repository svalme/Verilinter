"""The one place a rule asks which symbol a name refers to."""
from __future__ import annotations

from ..semantic.symbol import Symbol


def named_symbol(scope: object, name: str | None) -> Symbol | None:
    """The symbol `name` refers to from `scope`: the nearest declaration outward, then a name an import brings in
    (`Scope.lookup_hierarchical`). A scope that has no such lookup is asked for its own `lookup`. An empty name or no
    scope gives None. A rule asks here and never calls a scope lookup itself."""
    if not name or scope is None:
        return None
    for lookup_name in ("lookup_hierarchical", "lookup"):
        lookup = getattr(scope, lookup_name, None)
        if callable(lookup):
            return lookup(name)
    return None
