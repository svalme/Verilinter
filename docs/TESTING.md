# Testing Guide

```bash
python -m pytest
```

This is an overview of what kind of tests exist and where new ones belong. For
what a specific rule's tests should cover, see the Rule Checklist in
`CONTRIBUTING.md`. For which tests exercise a given `tests/data/` fixture, see
`FIXTURE_USAGE.md`.

## Test taxonomy

**Rule-level tests** (`tests/rules/<category>/test_*.py`) are the bulk of the
suite, one file per rule category. Each rule typically gets: a `rule.code` /
`rule.message` identity check, `applies()` unit tests against synthetic
`Mock(spec=BaseVNode)` nodes or hand-built `Context` stacks (see
`tests/support/syntax_context_builders.py` for reusable ancestor-context
builders), and at least one "against a real parsed file" test pointed at a
`tests/data/` fixture.

**Infrastructure unit tests**, one per architectural layer:

- `tests/walk/` -- the `Walker`/`Context` mechanics, plus `print_tree_test.py`'s
  AST snapshot tests (see Golden files below).
- `tests/vnodes/` -- `vnode_factory` registration and vnode-specific logic.
- `tests/handlers/` -- dispatch/handler registration, and integration tests
  that run a handler against a real parsed file.
- `tests/semantic/` -- the `SymbolTable` in isolation.

**Integration tests via the shared harness** (`tests/test_rule_case_harness.py`
and others) -- see Parsing patterns below.

**End-to-end CLI tests** (`tests/test_run_lint.py`, the largest file) -- drive
the actual `run()`/`main()` entry point per fixture: diagnostics content, exit
codes, stdout/stderr formatting, parallel vs. sequential jobs, rule-profile /
rule-selection plumbing.

**Cross-cutting suites**:

- `test_rule_overlap_harness.py` / `test_rule_overlap_metadata.py` --
  intentional overlap between rules and false-positive boundaries.
- `test_rule_registration.py` / `test_registration_files.py` -- metadata
  consistency (every rule file registered, codes/categories well-formed)
  across the whole rule set.
- `test_cli_features.py`, `test_multi_file_lint.py`, `test_analysis_store.py`
  -- CLI flags/output formats, multi-file/cross-file rules, and caching
  correctness respectively.
- `test_sv_adapter.py` -- the SystemVerilog adapter layer.

**Fixture-integrity tests**:

- `test_fixture_validity.py` -- every file in `tests/data/` must parse with
  pyslang without error-level diagnostics. A fixture that intentionally
  exercises parser recovery belongs in that file's
  `INTENTIONAL_PARSE_ERROR_FIXTURES` allowlist with a comment explaining why,
  not silently passing (or silently failing) this check.
- `test_fixture_usage_doc.py` -- keeps `FIXTURE_USAGE.md` in sync with actual
  fixture references (see Golden files below).

## Parsing patterns

Two ways to get RTL text through the walker coexist in the suite:

1. **Bespoke inline setup**: a test file builds its own `SymbolTable` +
   `Context` + `Walker(dispatch)`, parses with `sl.SyntaxTree.fromText(...)` or
   `fromFile(...)`, and calls `walker.walk(...)` directly. This is still the
   majority pattern in `tests/rules/`.
2. **Shared harness** (`tests/support/lint_harness.py`, exposed via
   `conftest.py` fixtures `lint_inline_case`, `lint_inline_case_spec`,
   `lint_temp_file_case`): runs text or real files through the same walker and
   all three rule runners (`rule_runner`, `symbol_rule_runner`,
   `module_rule_runner`), returning a `LintCaseResult` with assertion helpers
   (`expect_code_count`, `expect_no_code`, `expect_files_for_code`,
   `expect_message_contains`, ...). See `tests/test_rule_case_harness.py` for
   examples.

**Prefer the shared harness for new tests that check a complete diagnostic
result** (count, file, location, message content) rather than hand-rolling the
walk. It exercises more of the real pipeline (all three rule runners, not just
one), and centralizes the parser-boundary logic in one place. Bespoke setup
remains reasonable for a narrow unit test of one rule's `applies()`/`report()`
methods where a full walk isn't needed.

Neither path currently rejects parser errors before walking -- a fixture or
inline snippet with a real syntax error can still produce *some* AST via
pyslang's error recovery, and an assertion can pass for reasons unrelated to
the RTL it's supposed to demonstrate. For checked-in fixtures,
`test_fixture_validity.py` closes this gap independently of which harness a
test uses. For inline snippets (`sl.SyntaxTree.fromText(...)` written directly
in a test body), no equivalent check exists yet.

## Golden files

Two things in this suite compare generated output against a checked-in file
and support the same regenerate convention:

```bash
UPDATE_EXPECTED=1 pytest tests/walk/print_tree_test.py    # tests/expected/*.snippets.txt, *.walk.txt
UPDATE_EXPECTED=1 pytest tests/test_fixture_usage_doc.py  # FIXTURE_USAGE.md
```

Regenerating overwrites the checked-in file so the diff is a deliberate,
reviewable record of what changed and why -- review it before committing
rather than trusting the regeneration blindly.

## Fixtures

`tests/data/` is a single directory shared by the whole suite; a fixture named
by one test file is frequently read by several others too (see
`FIXTURE_USAGE.md` for the current map, including any fixtures nothing
references at all). Two implications when touching a fixture:

- Check `FIXTURE_USAGE.md` first -- a change intended for one test can shift
  diagnostics in every other test that reads the same file.
- The fixture must still parse cleanly (`test_fixture_validity.py` enforces
  this). If a change makes it exercise a genuinely different construct, keep
  the file's name and purpose aligned, or add a new fixture instead of
  repurposing one that other tests already depend on.
