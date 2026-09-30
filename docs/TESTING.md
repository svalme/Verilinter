# Testing Guide

```bash
python -m pytest
```

This is an overview of what kind of tests exist and where new ones belong. For
what a specific rule's tests should cover, see the Rule Checklist in
`CONTRIBUTING.md`. For which tests exercise a given `tests/data/` fixture, see
`FIXTURE_USAGE.md`.

## Test taxonomy

**Rule-level tests** (`tests/rules/`) are the bulk of the suite:
- `tests/rules/<category>/test_*.py`: modular per-rule test files across 18 categories.
- `tests/rules/overlap/`: rule collision, precedence boundaries, and suppression interaction tests (`test_rule_overlap_harness.py`, `test_rule_overlap_metadata.py`).
- `tests/rules/`: rule runners (`test_rule_runner.py`, `test_symbol_rule_runner.py`, `test_module_rule_runner.py`, `test_profiles.py`).

**Handler tests** (`tests/handlers/`):
Organized by subsystem domain, with nested `unit/`, `integration/`, and `regressions/` subdirectories:
- `identifier/`: token dispatch (`unit/`), symbol table interactions (`integration/`), and scoping edge cases (`regressions/`).
- `hierarchy/`: instantiation handler (`unit/`) and ANSI port inheritance across commas (`regressions/`).
- `procedural/`: case generate and for loop handlers (`unit/`) and task body execution ordering (`regressions/`).
- `declarations/`: function, package import, and primitive handlers (`unit/`).
- `core/`: base handler abstractions (`unit/`).

**Infrastructure unit tests**:
- `tests/walk/`: the `Walker`/`Context` mechanics, plus `print_tree_test.py`'s AST snapshot tests (see Golden files below).
- `tests/vnodes/`: `vnode_factory` registration and vnode-specific logic.
- `tests/semantic/`: the `SymbolTable` in isolation.
- `tests/unit/`: `test_sv_adapter.py` for SystemVerilog AST adapter extraction, `test_expression_engine.py` for constant folding and width evaluation, and `test_traversal_guard.py` for active-path cycle immunity, recursion bounding, and PyBind11 address recycling.

**Integration tests** (`tests/integration/`):
- `test_multi_file_lint.py`: multi-file / cross-file linting.
- `test_representative_rtl_examples.py` & `test_representative_rtl_defective_variants.py`: realistic clean RTL designs and defective variants.
- `test_rule_case_harness.py`: integration tests for the shared harness.

**CLI & execution mode tests** (`tests/cli/`):
- `test_run_lint.py`: end-to-end `run()`/`main()` entry point, diagnostics content, exit codes, stdout/stderr formatting.
- `test_cli_features.py`: CLI flags, file discovery, excludes, summary tables.
- `test_cli_execution_modes.py`: sequential vs. multiprocessing equivalence.

**Storage & caching tests** (`tests/storage/`):
- `test_analysis_store.py`: SQLite cache persistence, hash keys, warm/cold cache reads.
- `test_scope_execution_modes.py`: transitive header invalidation, include directory shadowing.

**Meta & fixture-integrity tests** (`tests/meta/`):
- `test_fixture_validity.py`: every file in `tests/data/` must parse with pyslang without error-level diagnostics. A fixture that intentionally exercises parser recovery belongs in that file's `INTENTIONAL_PARSE_ERROR_FIXTURES` allowlist with an explanatory comment.
- `test_fixture_usage_doc.py`: keeps `FIXTURE_USAGE.md` in sync with actual fixture references.
- `test_rule_registration.py` & `test_registration_files.py`: rule and handler manifest registration consistency.
- `test_mock_traversal_safety.py`: verifies exported query functions and context stack terminate on synthetic cyclic mocks.
- `test_recursion_and_depth_hygiene.py`: static AST analysis verifying that every recursive function across `src/pkg/` is guarded by `@guarded_traversal`/`@guarded_generator` or an explicit bounded depth check, and that all AST traversal `while` loops enforce bounded iteration or depth ceilings.
- `test_parser_boundary.py`: static AST analysis verifying that `pyslang` is imported only inside `src/pkg/parser/`, that no code outside the parser reads `<vnode>.raw.<field>` other than `.kind`, and that `run_lint.py` imports parsing entry points only from `pkg.parser.parse`.
- `test_timing_assertion_hygiene.py`: verifies that no test reads the wall clock directly; time budgets go through `terminates_within` (see below).

**Stress & loop immunity tests** (`tests/stress/`):
- `test_ast_cyclical_stress.py`: runs cyclical graph stress tests across all exported syntax query functions, rule-level statement latch analyzers, combinational loop DFS, and circular module instantiation DFS (single-node self-loops, multi-node cyclic rings, cyclic expressions, 500-node graph chains, and cyclic generators) to verify complete loop immunity and sub-second termination without `RecursionError` or hangs.
- `test_ast_malformed_stress.py`: malformed AST stress tests covering pathological parser error recovery trees, deep nesting beyond traversal limits, broken node attributes, cyclic scope hierarchies, cyclic context chains, and walker resilience.

## Pytest markers

Markers registered in `pyproject.toml`:
- `unit`: low-level unit tests for AST nodes, context, walker, adapter, handlers.
- `handlers`: syntax node handlers and scope resolution.
- `rules`: linter rule logic and applies checks.
- `overlap`: rule collision and precedence boundary checks.
- `cli`: command-line interface, formatting, and options.
- `storage`: caching, analysis store, and SQLite persistence.
- `integration`: multi-file, representative RTL, and end-to-end linting.
- `meta`: fixture validity, registration manifest checks, and doc sync.
- `stress`: malformed AST, cyclical graph, and loop immunity stress tests.

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

For those narrow tests, build syntax ancestors with `tests/support/fakes.py`
(`FakeNode`, `FakeVNode`, `fake_vnode`) or the shared builders in
`tests/support/syntax_context_builders.py`, not `Mock`. A `FakeNode` raises
`AttributeError` for a field the test did not set, so `getattr(raw, "field", None)`
in a parser helper yields `None` as it does on a real pyslang node; a bare `Mock`
returns a truthy child `Mock` there. Fakes are not `pyslang` instances, so
`raw_node_children` does not walk them; use a parsed snippet for tests that
need real children.

Neither path currently rejects parser errors before walking -- a fixture or
inline snippet with a real syntax error can still produce *some* AST via
pyslang's error recovery, and an assertion can pass for reasons unrelated to
the RTL it's supposed to demonstrate. For checked-in fixtures,
`test_fixture_validity.py` closes this gap independently of which harness a
test uses. For inline snippets (`sl.SyntaxTree.fromText(...)` written directly
in a test body), no equivalent check exists yet.

## Termination and time budgets

Stress and traversal-safety tests check that code returns on cyclic or deeply
nested input. Use `terminates_within` from `tests/support/termination.py` for
that check, not a hand-written stopwatch:

```python
with terminates_within():          # label defaults to the running test id
    assert unwrap_parentheses(cyclic) is cyclic
```

- A real non-termination bug hangs or raises `RecursionError`; an exception
  inside the block propagates unchanged and is never reported as a timing failure.
- Exceeding the budget raises `TerminationBudgetExceeded`, whose message says the
  code returned (slowness, not a loop) and how to tell load from a regression:
  rerun the test alone.
- `DEFAULT_BUDGET_S` is a generous ceiling for the small synthetic inputs in
  stress tests. Pass `budget_s=` for a test that does more work.
- Set `VERILINTER_TEST_TIME_SCALE` (for example `3`) to scale every budget on a
  loaded machine or slow CI runner.

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
