# Verilinter Rule Catalog

This file is the current inventory of implemented lint rules and the cases they cover.

## Rule Template

Use this template when adding a new rule entry:

Rendered example:

| Rule | Code | Covers | Implemented By | Tests | Known Limitations |
|---|---|---|---|---|---|
| Short rule name | `RULE_CODE` | One-sentence description of the cases the rule flags. | `src/pkg/rules/.../rule_file.py` | `tests/.../test_file.py` | Any important gaps, heuristics, or current behavior quirks. |

Copy/paste template:

```md
| Rule | Code | Covers | Implemented By | Tests | Known Limitations |
|---|---|---|---|---|---|
| Short rule name | `RULE_CODE` | One-sentence description of the cases the rule flags. | `src/pkg/rules/.../rule_file.py` | `tests/.../test_file.py` | Any important gaps, heuristics, or current behavior quirks. |
```

Guidelines:

- Keep `Covers` tied to what the current implementation actually does, not what we intend it to do later.
- Use repo-relative paths in `Implemented By` and `Tests`.
- If a rule has no meaningful current limitation, write `None noted`.
- If a rule does not yet define a dedicated diagnostic code, say so explicitly instead of inventing one here.

## Syntax Rules

These run during tree traversal and fire based on the current vnode plus its walk context.

| Rule | Code | Covers | Implemented By | Tests | Known Limitations |
|---|---|---|---|---|---|
| Non-blocking assignment in combinational logic | `NO_NONBLOCKING_COMBINATIONAL` | Flags `<=` inside `always_comb` blocks. | `src/pkg/rules/syntax/no_nonblocking_comb.py` | `tests/rules/syntax/test_rules.py` | Only checks `always_comb`; does not currently cover broader combinational-style heuristics outside that context. |
| Blocking assignment in sequential logic | `NO_BLOCKING_SEQUENTIAL` | Flags `=` inside `always` blocks used for sequential logic. | `src/pkg/rules/syntax/no_blocking_sequential_logic.py` | `tests/rules/syntax/test_rules.py` | Currently keyed off the `ALWAYS` context flag; does not distinguish every possible sequential-style construct. |
| Missing default in case statement | `DEFAULT_CASE` | Flags `case ... endcase` constructs that do not include a `default` branch. | `src/pkg/rules/syntax/default_case.py` | `tests/rules/syntax/test_rules.py`, `tests/handlers/test_case_generate_handler.py` | Current implementation is tied to the existing case/default context flags and should be revisited if case handling broadens. |
| `casex` / `casez` usage | `NO_CASEX_CASEZ` | Flags `casex` and `casez`, which can hide X/Z-related matching issues. | `src/pkg/rules/syntax/no_casex_casez.py` | `tests/rules/syntax/test_rules.py`, `tests/test_run_lint.py` | Pure keyword check; does not distinguish project-specific allowed uses. |
| Mixed assignment style in one procedural block | `NO_MIXED_ASSIGNMENT_STYLE` | Flags procedural blocks that contain both blocking (`=`) and non-blocking (`<=`) assignments. Reports once per mixed block. | `src/pkg/rules/syntax/no_mixed_assignment_style.py` | `tests/rules/syntax/test_rules.py`, `tests/test_run_lint.py` | Reports once per mixed block and ignores nested procedural blocks while scanning an enclosing block. |

## Symbol Rules

These run after the walk against the accumulated symbol table for the linted file set.

| Rule | Code | Covers | Implemented By | Tests | Known Limitations |
|---|---|---|---|---|---|
| Unused variable | `UNUSED_VARIABLE` | Flags declared variables that are never used. | `src/pkg/rules/symbol/unused_variable_rule.py` | `tests/rules/symbol/test_unused_variable_rule.py` | Only checks symbols whose `kind` is `"variable"`. |
| Read before write | `READ_BEFORE_WRITE` | Flags variables that are read before they have any recorded write. | `src/pkg/rules/symbol/read_before_write_rule.py` | `tests/rules/symbol/test_read_before_write_rule.py` | Currently only recognizes direct identifier assignment targets as writes; more complex lvalues may need richer write-context handling. |
| Undeclared variable | `UNDECLARED_VARIABLE` | Flags variables that are used but never declared. | `src/pkg/rules/symbol/undeclared_variable.py` | `tests/rules/symbol/test_undeclared_variable.py` | Flags based on missing declarations in the symbol table. |
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
