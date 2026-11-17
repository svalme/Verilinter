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
- `tests/unit/`: `test_sv_adapter.py` for SystemVerilog AST adapter extraction, `test_expression_engine.py` for constant folding and width evaluation, and `test_traversal_guard.py` for active-path cycle immunity, recursion bounding, and PyBind11 address recycling, and `test_node_cache.py` for identity-checked per-node memoization.

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
- `test_store_structure.py`: the cache, the run history and the connection stay separate modules, and each works without the other.
- `test_scope_execution_modes.py`: transitive header invalidation, include directory shadowing.

**Meta & fixture-integrity tests** (`tests/meta/`):
- `test_fixture_validity.py`: every file in `tests/data/` must parse with pyslang without error-level diagnostics. A fixture that intentionally exercises parser recovery belongs in that file's `INTENTIONAL_PARSE_ERROR_FIXTURES` allowlist with an explanatory comment.
- `test_fixture_usage_doc.py`: keeps `FIXTURE_USAGE.md` in sync with actual fixture references.
- `test_rule_registration.py` & `test_registration_files.py`: rule and handler manifest registration consistency.
- `test_mock_traversal_safety.py`: verifies exported query functions and context stack terminate on synthetic cyclic mocks.
- `test_recursion_and_depth_hygiene.py`: static AST analysis verifying that every recursive function across `src/pkg/` is guarded by `@guarded_traversal`/`@guarded_generator` or an explicit bounded depth check, and that all AST traversal `while` loops enforce bounded iteration or depth ceilings.
- `test_parser_boundary.py`: static AST analysis verifying that `pyslang` is imported only inside `src/pkg/parser/`, that no code outside the parser reads `<vnode>.raw.<field>` other than `.kind`, and that `run_lint.py` imports parsing entry points only from `pkg.parser.parse`.
- `test_cache_and_scratch_hygiene.py`: static AST analysis verifying that `id()` is not used outside the allowlisted traversal and registry files (memoization uses `node_cache`), and that tests create scratch directories only through `make_scratch`.
- `test_timing_assertion_hygiene.py`: verifies that no test reads the wall clock directly; time budgets go through `terminates_within` (see below).

**Stress & loop immunity tests** (`tests/stress/`):
- `test_ast_cyclical_stress.py`: runs cyclical graph stress tests across all exported syntax query functions, rule-level statement latch analyzers, combinational loop DFS, and circular module instantiation DFS (single-node self-loops, multi-node cyclic rings, cyclic expressions, 500-node graph chains, and cyclic generators) to verify complete loop immunity and termination within the `terminates_within` budget without `RecursionError` or hangs.
- `test_ast_malformed_stress.py`: malformed AST stress tests covering pathological parser error recovery trees, deep nesting beyond traversal limits, broken node attributes, cyclic scope hierarchies, cyclic context chains, and walker resilience.
- `test_harness_nesting_stress.py`: end-to-end extreme nesting and stress tests through the full `LintPipeline` under `terminates_within` covering 60 levels of nested conditionals, 50 levels of nested case statements, 100-level parenthesized expressions, 80-level concatenations, 50-level generate blocks, and 50-module instantiation hierarchy chains.

## File organization

Place every new test file in the folder or subfolder that matches the code it covers, and create the folder (with an `__init__.py`) when none fits; test folders mirror the source folders (`tests/rules/<category>/<theme>/`). A directory with about 14 or more test files is the point to group them.

A test file stays under 700 lines (`tests/meta/test_file_size_limits.py` fails above that) and covers one concern: one rule, one subsystem, or one group of closely related rules. Do not collect many rules' tests into one module that "everything reports to".

- A file that grows past the limit is split by concern and the pieces are grouped in a folder named for the group, for example `tests/cli/run_lint/` (instance, signal, statement and net rules), `tests/semantic/symbols/`, `tests/rules/width_and_signedness/assignment/`, `tests/rules/connectivity_and_hierarchy/undriven/`.
- Node-rule tests live next to the rule's category: `tests/rules/<category>/test_<category>_node_rules.py`, one class per rule; a category with many rules is split by theme (`tests/rules/simulation_vs_synthesis/test_simulation_procedural_constructs.py`).
- Helpers or fixtures used by more than one test file go in `tests/support/`; a helper used by one file stays in that file.
- A test file that reads `tests/data/` builds the path from `Path(__file__)`, so moving it deeper needs one more `.parent` (or a higher `.parents[n]`).
- After moving or splitting test files, regenerate `docs/FIXTURE_USAGE.md` (`UPDATE_EXPECTED=1 pytest tests/meta/test_fixture_usage_doc.py`) and update the test paths in the rule's row in `docs/RULES.md`.

## Breadth catalog

Each rule has one breadth file, `tests/breadth/<rule category>/<RULE_CODE>.sv`, kept apart from the unit tests. It lists, as small SystemVerilog snippets, what the rule must report, what it must not report, and the boundary between them, so a change that makes the rule too narrow or too broad fails a named breadth case. A breadth case starts with a marker line:

- `// breadth: reports | <what the rule must catch>`: a miss means the rule is too narrow.
- `// breadth: clean | <what the rule must not report>`: a finding means the rule is too broad.
- `// breadth: gap | <a known miss>`: a strict expected failure. Without `// expect:` it is a breadth case the rule should catch but does not yet; promote it to `reports` when the rule catches it. With `// expect: 0` it is one the rule should not report but still does (too broad); promote it to `clean` when the rule stops reporting it.
- `// pair: <name>` on one `reports` and one `clean` breadth case ties a boundary: the two differ in the one detail that decides the outcome.
- `// expect: N` gives the number of findings of the rule (default 1 for `reports` and `gap`, 0 for `clean`; `// expect: 0` on a `gap` marks a too-broad miss).

`tests/breadth/test_rule_breadth.py` runs them; `tests/meta/test_breadth_coverage.py` requires every rule to have a file with at least one `reports` and one `clean` breadth case, in its category folder. `tests/breadth/RULE_BREADTH_STATUS.txt` lists every rule with `yes` or `no` for whether it has a breadth file, and the meta test checks each line against the files; a `no` only becomes `yes`, so a new rule is listed as `yes` together with its breadth cases. The table below gives the case counts of the rules that have a file. When a fix or a verdict shows a case the catalog lacks (a false positive, a missed defect), add it to the rule's file in the same change.

Rules with a breadth file (generated; regenerate with `UPDATE_EXPECTED=1 pytest tests/meta/test_breadth_catalog_doc.py` after adding or changing a breadth file):

<!-- BEGIN BREADTH COVERAGE (generated by tests/meta/test_breadth_catalog_doc.py) -->

36 of 172 rules have a breadth file.

| Category | Rules | With breadth cases | Without a breadth file |
|---|---|---|---|
| `arrays_and_indexing` | 6 | 1 | 5 |
| `assertions_and_verification` | 9 | 0 | 9 |
| `clock_and_reset` | 3 | 0 | 3 |
| `combinational_logic` | 13 | 5 | 8 |
| `conditional_and_case_statements` | 15 | 1 | 14 |
| `connectivity_and_hierarchy` | 21 | 4 | 17 |
| `declarations_and_types` | 11 | 2 | 9 |
| `fsms` | 3 | 0 | 3 |
| `latches` | 2 | 0 | 2 |
| `maintainability_and_complexity` | 5 | 1 | 4 |
| `naming_and_style` | 9 | 2 | 7 |
| `operators_and_expressions` | 4 | 0 | 4 |
| `parameters_and_generate_logic` | 10 | 0 | 10 |
| `sequential_logic` | 4 | 0 | 4 |
| `simulation_vs_synthesis` | 37 | 2 | 35 |
| `syntax_and_structure` | 2 | 0 | 2 |
| `unused_and_dead_code` | 4 | 4 | 0 |
| `width_and_signedness` | 14 | 14 | 0 |

| Rule | Category | `reports` | `clean` | `gap` | Pairs |
|---|---|---|---|---|---|
| `CONSTANT_INDEX_OUT_OF_RANGE` | `arrays_and_indexing` | 4 | 3 | 1 | 1 |
| `COMBINATIONAL_LOOP` | `combinational_logic` | 3 | 3 | 0 | 2 |
| `NO_LATCH_IN_ALWAYS_COMB` | `combinational_logic` | 4 | 2 | 0 | 1 |
| `NO_MULTIPLE_DRIVERS` | `combinational_logic` | 2 | 3 | 0 | 1 |
| `NO_SELF_ASSIGNMENT` | `combinational_logic` | 3 | 2 | 0 | 1 |
| `READ_BEFORE_WRITE` | `combinational_logic` | 2 | 4 | 0 | 1 |
| `NO_UNIQUE_PRIORITY_CASE` | `conditional_and_case_statements` | 5 | 4 | 0 | 3 |
| `NO_UNCONNECTED_INSTANCE_PORTS` | `connectivity_and_hierarchy` | 8 | 6 | 3 | 3 |
| `NO_UNDRIVEN_OUTPUT_PORT` | `connectivity_and_hierarchy` | 5 | 12 | 1 | 3 |
| `NO_UNDRIVEN_SIGNAL` | `connectivity_and_hierarchy` | 3 | 3 | 0 | 0 |
| `UNREAD_INSTANCE_OUTPUT` | `connectivity_and_hierarchy` | 6 | 9 | 3 | 2 |
| `NO_IMPLICIT_NET` | `declarations_and_types` | 3 | 3 | 0 | 1 |
| `REDECLARED_VARIABLE` | `declarations_and_types` | 3 | 3 | 0 | 1 |
| `EMPTY_CONDITIONAL_BRANCH` | `maintainability_and_complexity` | 3 | 2 | 0 | 1 |
| `INSTANCE_NAME_PREFIX` | `naming_and_style` | 4 | 4 | 1 | 4 |
| `RESET_SIGNAL_NAMING` | `naming_and_style` | 4 | 5 | 1 | 3 |
| `MISSING_TIMESCALE_DIRECTIVE` | `simulation_vs_synthesis` | 3 | 5 | 0 | 3 |
| `PROCASSINIT` | `simulation_vs_synthesis` | 5 | 11 | 1 | 4 |
| `NO_UNUSED_PARAMETER` | `unused_and_dead_code` | 6 | 10 | 1 | 3 |
| `NO_WRITE_ONLY_INPUT_PORT` | `unused_and_dead_code` | 4 | 9 | 0 | 3 |
| `NO_WRITE_ONLY_VARIABLE` | `unused_and_dead_code` | 7 | 19 | 1 | 3 |
| `UNUSED_VARIABLE` | `unused_and_dead_code` | 18 | 25 | 1 | 13 |
| `ARITHMETIC_RESULT_TRUNCATION` | `width_and_signedness` | 21 | 11 | 9 | 9 |
| `ASSIGNMENT_SIGNEDNESS_MISMATCH` | `width_and_signedness` | 10 | 7 | 2 | 3 |
| `ASSIGNMENT_TRUNCATION` | `width_and_signedness` | 21 | 13 | 2 | 7 |
| `ASSIGNMENT_WIDTH_MISMATCH` | `width_and_signedness` | 4 | 3 | 0 | 1 |
| `COMPARISON_ALWAYS_CONSTANT` | `width_and_signedness` | 13 | 15 | 5 | 11 |
| `COMPARISON_SIGNEDNESS_MISMATCH` | `width_and_signedness` | 15 | 15 | 4 | 9 |
| `COMPARISON_WIDTH_MISMATCH` | `width_and_signedness` | 27 | 22 | 2 | 17 |
| `EXPLICIT_XZ_LITERAL` | `width_and_signedness` | 10 | 8 | 1 | 5 |
| `LITERAL_WIDTH_OVERFLOW` | `width_and_signedness` | 10 | 7 | 1 | 4 |
| `NO_UNSIZED_LITERAL` | `width_and_signedness` | 4 | 9 | 3 | 4 |
| `PORT_CONNECTION_SIGNEDNESS_MISMATCH` | `width_and_signedness` | 9 | 5 | 2 | 3 |
| `PORT_CONNECTION_WIDTH_MISMATCH` | `width_and_signedness` | 3 | 4 | 0 | 1 |
| `PORT_CONNECTION_WIDTH_UNKNOWN` | `width_and_signedness` | 3 | 7 | 0 | 1 |
| `SHIFT_AMOUNT_OUT_OF_RANGE` | `width_and_signedness` | 19 | 14 | 5 | 11 |

<!-- END BREADTH COVERAGE -->

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
   `lint_temp_file_case`, `lint_paired_case`): runs text or real files through the same walker and
   all three rule runners (`rule_runner`, `symbol_rule_runner`,
   `module_rule_runner`), returning a `LintCaseResult` with assertion helpers
   (`expect_code_count`, `expect_no_code`, `expect_clean`, `expect_diagnostics`,
   `expect_files_for_code`, `expect_message_contains`, ...). See `tests/unit/test_lint_harness.py`
   and `tests/integration/test_rule_case_harness.py` for examples.

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

## Isolation standards

Each test must start from a known state and leave nothing behind for a later
test, run, or the code under test to pick up.

- **On-disk scratch space** (SQLite stores, CLI output files, generated HDL)
  comes from `make_scratch(root, name)` in `tests/support/scratch.py` or from
  the `tmp_path` fixture. Never `mkdir` under `tests/_tmp_*` by hand. An autouse
  fixture in `tests/conftest.py` removes every directory registered through
  `make_scratch` when the test ends, and clears the `_tmp_*` roots once at
  session start so a crashed run cannot leave data behind. Windows read-only
  flags are cleared during removal.
- Nothing reads scratch directories after a test, because assertions run inside
  the test. To inspect them while debugging, run with `VERILINTER_KEEP_SCRATCH=1`;
  the next run without it removes them.
- **One store per test.** Every SQLite store lives in its own scratch directory,
  so a cache hit or miss never depends on an earlier test. A test about warm
  versus cold behavior creates both runs inside the same directory, deliberately.
- **No ambient state.** Library code reads no environment variables or home
  directory caches; the only configuration lookup is `.verilinter.toml` in the
  working directory. Tests that change the working directory use
  `monkeypatch.chdir` so it is restored.
- **No process-wide memoization.** Cached analysis results live on the
  per-module `Context` data and are keyed through `node_cache` (see
  `CONTRIBUTING.md`), so a new module or run always starts empty. Module-level
  `lru_cache` or global dicts holding analysis results are not allowed.
- **Concurrency tests do not rely on one lucky interleaving.** A test that starts
  competing processes repeats the round, each with a fresh store, and a test of a
  specific lock path holds the contended lock deterministically (see
  `test_open_waits_for_a_competing_writer_instead_of_failing`). A single round of
  contenders can pass for months and still hide a race.
- **A failure that passes on rerun is a bug,** not noise. Run the test alone and
  in the full suite, with and without `VERILINTER_TEST_TIME_SCALE`, and look for
  state shared between runs before retrying or loosening an assertion.

`tests/meta/test_cache_and_scratch_hygiene.py` enforces the `id()` key rule and
the `make_scratch` rule.

## Golden files

Two things in this suite compare generated output against a checked-in file
and support the same regenerate convention:

```bash
UPDATE_EXPECTED=1 pytest tests/walk/print_tree_test.py    # tests/expected/*.snippets.txt, *.walk.txt
UPDATE_EXPECTED=1 pytest tests/meta/test_fixture_usage_doc.py  # FIXTURE_USAGE.md
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
