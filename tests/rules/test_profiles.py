import pytest

from src.pkg.rules.profiles import available_rule_profiles, rule_selection_for_profile


class TestRuleProfiles:
    def test_available_rule_profiles_returns_expected_names(self) -> None:
        assert available_rule_profiles() == (
            "all",
            "rtl_strict",
            "sv_rtl_subset",
            "legacy_verilog",
        )

    def test_all_profile_returns_open_selection(self) -> None:
        selection = rule_selection_for_profile("all")

        assert selection.enabled_codes is None
        assert selection.enabled_categories is None
        assert selection.enabled_profiles is None

    def test_named_profile_sets_enabled_profiles(self) -> None:
        selection = rule_selection_for_profile("sv_rtl_subset")

        assert selection.enabled_profiles == frozenset({"sv_rtl_subset"})

    def test_unknown_profile_raises_clear_error(self) -> None:
        with pytest.raises(ValueError, match="unknown rule profile 'nope'"):
            rule_selection_for_profile("nope")
