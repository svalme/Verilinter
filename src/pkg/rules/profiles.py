from __future__ import annotations

from .rule_selection import RuleSelection

_BUILTIN_RULE_PROFILES: dict[str, RuleSelection] = {
    "all": RuleSelection(),
    "rtl_strict": RuleSelection(enabled_profiles=frozenset({"rtl_strict"})),
    "sv_rtl_subset": RuleSelection(enabled_profiles=frozenset({"sv_rtl_subset"})),
    "legacy_verilog": RuleSelection(enabled_profiles=frozenset({"legacy_verilog"})),
}


def available_rule_profiles() -> tuple[str, ...]:
    """Return the stable set of built-in internal rule-profile names."""

    return tuple(_BUILTIN_RULE_PROFILES)


def rule_selection_for_profile(name: str) -> RuleSelection:
    """Return the built-in RuleSelection for `name`.

    This is intentionally an internal convenience layer for code/tests. The CLI
    still does not expose profile selection yet.
    """

    try:
        return _BUILTIN_RULE_PROFILES[name]
    except KeyError as exc:
        available = ", ".join(available_rule_profiles())
        raise ValueError(f"unknown rule profile '{name}'; available profiles: {available}") from exc
