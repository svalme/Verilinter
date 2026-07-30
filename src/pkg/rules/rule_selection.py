from __future__ import annotations

from dataclasses import dataclass

from .base_diagnostic import BaseDiagnostic


@dataclass(frozen=True)
class RuleSelection:
    """Optional runner-side filter for rule metadata.

    This is intentionally lightweight and default-open: omitted filters do not
    constrain the rule set, and untagged rules stay enabled under profile
    filtering so profile support can roll out incrementally.
    """

    enabled_codes: frozenset[str] | None = None
    enabled_categories: frozenset[str] | None = None
    enabled_profiles: frozenset[str] | None = None

    def allows(self, rule: BaseDiagnostic) -> bool:
        if self.enabled_codes is not None and rule.code not in self.enabled_codes:
            return False

        if self.enabled_categories is not None and rule.category not in self.enabled_categories:
            return False

        if self.enabled_profiles is None:
            return True

        if not rule.default_profiles:
            return True

        return not self.enabled_profiles.isdisjoint(rule.default_profiles)
