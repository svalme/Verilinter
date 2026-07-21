from src.pkg.rules.register_rules import rule_runner


def test_shared_rule_runner_includes_all_expected_syntax_rule_codes() -> None:
    codes = {rule.code for rule in rule_runner._rules}

    assert {
        "NO_BLOCKING_SEQUENTIAL",
        "NO_NONBLOCKING_COMBINATIONAL",
        "DEFAULT_CASE",
        "NO_CASEX_CASEZ",
        "NO_FULL_PARALLEL_CASE",
        "NO_MIXED_ASSIGNMENT_STYLE",
        "NO_INITIAL_BLOCK",
        "NO_FINAL_BLOCK",
        "NO_ALWAYS_LATCH",
        "NO_CASE_GENERATE",
        "NO_UNIQUE_PRIORITY_CASE",
        "NO_LATCH_IN_ALWAYS_COMB",
        "NO_DEFPARAM",
    }.issubset(codes)
