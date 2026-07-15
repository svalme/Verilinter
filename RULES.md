# Verilinter Rule Catalog

This file is the current inventory of implemented lint rules and the cases they cover.

## Rule Template

Use this template when adding a new rule entry:

Rendered example:

| Rule | Code | Match Level | Covers | Implemented By | Tests | Known Limitations |
|---|---|---|---|---|---|---|
| Short rule name | `RULE_CODE` | `token`, `node`, or `block` | One-sentence description of the cases the rule flags. | `src/pkg/rules/.../rule_file.py` | `tests/.../test_file.py` | Any important gaps, heuristics, or current behavior quirks. |

Copy/paste template:

```md
| Rule | Code | Match Level | Covers | Implemented By | Tests | Known Limitations |
|---|---|---|---|---|---|---|
| Short rule name | `RULE_CODE` | `token`, `node`, or `block` | One-sentence description of the cases the rule flags. | `src/pkg/rules/.../rule_file.py` | `tests/.../test_file.py` | Any important gaps, heuristics, or current behavior quirks. |
```

Guidelines:

- Keep `Covers` tied to what the current implementation actually does, not what we intend it to do later.
- `Match Level` means what kind of vnode the rule anchors its diagnostic to:
  `token` for a punctuation/keyword token, `node` for a syntax node, `block` for a whole procedural or structural construct.
- Use repo-relative paths in `Implemented By` and `Tests`.
- If a rule has no meaningful current limitation, write `None noted`.
- If a rule does not yet define a dedicated diagnostic code, say so explicitly instead of inventing one here.

## Syntax Rules

These run during tree traversal and fire based on the current vnode plus its walk context.

| Rule | Code | Match Level | Covers | Implemented By | Tests | Known Limitations |
|---|---|---|---|---|---|---|
| Non-blocking assignment in combinational logic | `NO_NONBLOCKING_COMBINATIONAL` | `token` | Flags `<=` inside `always_comb` blocks. | `src/pkg/rules/syntax/no_nonblocking_comb.py` | `tests/rules/syntax/test_rules.py` | Only checks `always_comb`; does not currently cover broader combinational-style heuristics outside that context. |
| Blocking assignment in sequential logic | `NO_BLOCKING_SEQUENTIAL` | `token` | Flags `=` inside `always` blocks used for sequential logic. | `src/pkg/rules/syntax/no_blocking_sequential_logic.py` | `tests/rules/syntax/test_rules.py` | Currently keyed off the `ALWAYS` context flag; does not distinguish every possible sequential-style construct. |
| Missing default in case statement | `DEFAULT_CASE` | `token` | Flags `case ... endcase` constructs that do not include a `default` branch. | `src/pkg/rules/syntax/default_case.py` | `tests/rules/syntax/test_rules.py`, `tests/handlers/test_case_generate_handler.py` | Current implementation is tied to the existing case/default context flags and should be revisited if case handling broadens. |
| `casex` / `casez` usage | `NO_CASEX_CASEZ` | `token` | Flags `casex` and `casez`, which can hide X/Z-related matching issues. | `src/pkg/rules/syntax/no_casex_casez.py` | `tests/rules/syntax/test_rules.py`, `tests/test_run_lint.py` | Pure keyword check; does not distinguish project-specific allowed uses. |
| `full_case` / `parallel_case` pragmas | `NO_FULL_PARALLEL_CASE` | `token` | Flags `case` statements preceded by `full_case` or `parallel_case` pragma comments. | `src/pkg/rules/syntax/no_full_parallel_case.py` | `tests/rules/syntax/test_rules.py`, `tests/test_run_lint.py`, `tests/test_rule_registration.py` | Current implementation only checks the immediately preceding source line for pragma text; same-line or more exotic pragma placements are not yet recognized. |
| `unique` / `priority` case usage | `NO_UNIQUE_PRIORITY_CASE` | `token` | Flags `unique case` and `priority case` keywords. | `src/pkg/rules/syntax/no_unique_priority_case.py` | `tests/rules/syntax/test_rules.py`, `tests/test_run_lint.py`, `tests/test_rule_registration.py` | Pure keyword check; does not distinguish project-specific cases where these modifiers are required by coding style. |
| Mixed assignment style in one procedural block | `NO_MIXED_ASSIGNMENT_STYLE` | `block` | Flags procedural blocks that contain both blocking (`=`) and non-blocking (`<=`) assignments. Reports once per mixed block. | `src/pkg/rules/syntax/no_mixed_assignment_style.py` | `tests/rules/syntax/test_rules.py`, `tests/test_run_lint.py` | Reports once per mixed block and ignores nested procedural blocks while scanning an enclosing block. |
| `initial` block usage | `NO_INITIAL_BLOCK` | `block` | Flags `initial` blocks, which are often undesirable in synthesizable RTL. | `src/pkg/rules/syntax/no_initial_block.py` | `tests/rules/syntax/test_rules.py`, `tests/test_rule_registration.py` | Intentionally broad; does not try to distinguish testbench code from synthesizable RTL contexts. |
| `final` block usage | `NO_FINAL_BLOCK` | `block` | Flags `final` blocks, which are generally not appropriate in synthesizable RTL flows. | `src/pkg/rules/syntax/no_final_block.py` | `tests/rules/syntax/test_rules.py`, `tests/test_run_lint.py`, `tests/test_rule_registration.py` | Intentionally broad; does not try to distinguish simulation-only code from synthesizable RTL contexts. |
| `always_latch` usage | `NO_ALWAYS_LATCH` | `block` | Flags `always_latch` procedural blocks. | `src/pkg/rules/syntax/no_always_latch.py` | `tests/rules/syntax/test_rules.py`, `tests/test_run_lint.py`, `tests/test_rule_registration.py` | Intentionally broad; treats all latch-oriented procedural blocks as undesirable rather than trying to infer whether a latch was intentional. |
| `case generate` usage | `NO_CASE_GENERATE` | `node` | Flags `case ... endcase` generate constructs. | `src/pkg/rules/syntax/no_case_generate.py` | `tests/rules/syntax/test_rules.py`, `tests/test_run_lint.py`, `tests/test_rule_registration.py` | Intentionally broad; treats `case generate` as a readability / structure smell rather than trying to infer whether it was the best structural choice. |

## Symbol Rules

These run after the walk against the accumulated symbol table for the linted file set.

| Rule | Code | Covers | Implemented By | Tests | Known Limitations |
|---|---|---|---|---|---|
| Unused variable | `UNUSED_VARIABLE` | Flags declared variables that are never used. | `src/pkg/rules/symbol/unused_variable_rule.py` | `tests/rules/symbol/test_unused_variable_rule.py` | Only checks symbols whose `kind` is `"variable"`. |
| Read before write | `READ_BEFORE_WRITE` | Flags variables that are read before they have any recorded write. | `src/pkg/rules/symbol/read_before_write_rule.py` | `tests/rules/symbol/test_read_before_write_rule.py` | Now treats compound assignments and increment/decrement forms as read+write events, but broader write-like contexts may still need richer access-mode modeling over time. |
| Undeclared variable | `UNDECLARED_VARIABLE` | Flags variables that are used but never declared. | `src/pkg/rules/symbol/undeclared_variable.py` | `tests/rules/symbol/test_undeclared_variable.py` | Current semantic model does not yet distinguish generic undeclared identifiers from language-level implicit nets, so this rule currently covers both. |
| Redeclared variable | `REDECLARED_VARIABLE` | Flags symbols declared more than once in the same scope. | `src/pkg/rules/symbol/redeclared_variable.py` | `tests/rules/symbol/test_redeclared_variable.py` | Message reports the first declaration line but not currently richer scope context. |

## Module / Cross-File Rules

These run after all files have been walked and use batch-level module tracking.

| Rule | Code | Covers | Implemented By | Tests | Known Limitations |
|---|---|---|---|---|---|
| Duplicate module definition | `DUPLICATE_MODULE` | Flags modules defined more than once across the linted file set. | `src/pkg/rules/module/duplicate_module_definition.py` | `tests/rules/module/test_duplicate_module_definition.py`, `tests/test_multi_file_lint.py` | Reports duplicates relative to the first-seen definition; current message is file-oriented rather than richer declaration-context-oriented. |
| Undefined module instantiation | `UNDEFINED_MODULE` | Flags instantiations whose module type is not defined anywhere in the linted file set. | `src/pkg/rules/module/undefined_module.py` | `tests/rules/module/test_undefined_module.py` | Depends on the module-reference tracking captured during the walk; limited to what the current instantiation handler records. |

## Notes

- The README gives a short feature summary; this file is the more complete rule inventory.
- If a new rule is added, update this file in the same change so the rule list stays accurate.
