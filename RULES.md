# Verilinter Rule Catalog

This file is the current inventory of implemented lint rules and the cases they cover.

## Rule Template

Use this template when adding a new rule entry:

Rendered example:

| Rule | Code | Language Scope | Match Level | Covers | Implemented By | Tests | Known Limitations |
|---|---|---|---|---|---|---|---|
| Short rule name | `RULE_CODE` | `Verilog`, `SystemVerilog`, or `Both` | `token`, `node`, or `block` | One-sentence description of the cases the rule flags. | `src/pkg/rules/.../rule_file.py` | `tests/.../test_file.py` | Any important gaps, heuristics, or current behavior quirks. |

Copy/paste template:

```md
| Rule | Code | Language Scope | Match Level | Covers | Implemented By | Tests | Known Limitations |
|---|---|---|---|---|---|---|---|
| Short rule name | `RULE_CODE` | `Verilog`, `SystemVerilog`, or `Both` | `token`, `node`, or `block` | One-sentence description of the cases the rule flags. | `src/pkg/rules/.../rule_file.py` | `tests/.../test_file.py` | Any important gaps, heuristics, or current behavior quirks. |
```

Guidelines:

- Keep `Covers` tied to what the current implementation actually does, not what we intend it to do later.
- `Language Scope` means the language family the current rule meaningfully applies to:
  `Verilog`, `SystemVerilog`, or `Both`.
- `Match Level` means what kind of vnode the rule anchors its diagnostic to:
  `token` for a punctuation/keyword token, `node` for a syntax node, `block` for a whole procedural or structural construct.
- Use repo-relative paths in `Implemented By` and `Tests`.
- If a rule has no meaningful current limitation, write `None noted`.
- If a rule does not yet define a dedicated diagnostic code, say so explicitly instead of inventing one here.

## Syntax Rules

These run during tree traversal and fire based on the current vnode plus its walk context.

| Rule | Code | Language Scope | Match Level | Covers | Implemented By | Tests | Known Limitations |
|---|---|---|---|---|---|---|---|
| Non-blocking assignment in combinational logic | `NO_NONBLOCKING_COMBINATIONAL` | `SystemVerilog` | `token` | Flags `<=` inside `always_comb` blocks. | `src/pkg/rules/syntax/no_nonblocking_comb.py` | `tests/rules/syntax/test_rules.py` | Only checks `always_comb`; does not currently cover broader combinational-style heuristics outside that context. |
| Blocking assignment in sequential logic | `NO_BLOCKING_SEQUENTIAL` | `Both` | `token` | Flags `=` inside `always` blocks used for sequential logic. | `src/pkg/rules/syntax/no_blocking_sequential_logic.py` | `tests/rules/syntax/test_rules.py` | Currently keyed off the `ALWAYS` context flag; does not distinguish every possible sequential-style construct. |
| Missing default in case statement | `DEFAULT_CASE` | `Both` | `token` | Flags `case ... endcase` constructs that do not include a `default` branch. | `src/pkg/rules/syntax/default_case.py` | `tests/rules/syntax/test_rules.py`, `tests/handlers/test_case_generate_handler.py` | Current implementation is tied to the existing case/default context flags and should be revisited if case handling broadens. |
| `casex` / `casez` usage | `NO_CASEX_CASEZ` | `Both` | `token` | Flags `casex` and `casez`, which can hide X/Z-related matching issues. | `src/pkg/rules/syntax/no_casex_casez.py` | `tests/rules/syntax/test_rules.py`, `tests/test_run_lint.py` | Pure keyword check; does not distinguish project-specific allowed uses. |
| `full_case` / `parallel_case` pragmas | `NO_FULL_PARALLEL_CASE` | `Both` | `token` | Flags `case` statements preceded by `full_case` or `parallel_case` pragma comments. | `src/pkg/rules/syntax/no_full_parallel_case.py` | `tests/rules/syntax/test_rules.py`, `tests/test_run_lint.py`, `tests/test_rule_registration.py` | Current implementation only checks the immediately preceding source line for pragma text; same-line or more exotic pragma placements are not yet recognized. |
| `unique` / `priority` case usage | `NO_UNIQUE_PRIORITY_CASE` | `SystemVerilog` | `token` | Flags `unique case` and `priority case` keywords. | `src/pkg/rules/syntax/no_unique_priority_case.py` | `tests/rules/syntax/test_rules.py`, `tests/test_run_lint.py`, `tests/test_rule_registration.py` | Pure keyword check; does not distinguish project-specific cases where these modifiers are required by coding style. |
| Mixed assignment style in one procedural block | `NO_MIXED_ASSIGNMENT_STYLE` | `Both` | `block` | Flags procedural blocks that contain both blocking (`=`) and non-blocking (`<=`) assignments. Reports once per mixed block. | `src/pkg/rules/syntax/no_mixed_assignment_style.py` | `tests/rules/syntax/test_rules.py`, `tests/test_run_lint.py` | Reports once per mixed block and ignores nested procedural blocks while scanning an enclosing block. |
| `initial` block usage | `NO_INITIAL_BLOCK` | `Both` | `block` | Flags `initial` blocks, which are often undesirable in synthesizable RTL. | `src/pkg/rules/syntax/no_initial_block.py` | `tests/rules/syntax/test_rules.py`, `tests/test_rule_registration.py` | Intentionally broad; does not try to distinguish testbench code from synthesizable RTL contexts. |
| `final` block usage | `NO_FINAL_BLOCK` | `SystemVerilog` | `block` | Flags `final` blocks, which are generally not appropriate in synthesizable RTL flows. | `src/pkg/rules/syntax/no_final_block.py` | `tests/rules/syntax/test_rules.py`, `tests/test_run_lint.py`, `tests/test_rule_registration.py` | Intentionally broad; does not try to distinguish simulation-only code from synthesizable RTL contexts. |
| `always_latch` usage | `NO_ALWAYS_LATCH` | `SystemVerilog` | `block` | Flags `always_latch` procedural blocks. | `src/pkg/rules/syntax/no_always_latch.py` | `tests/rules/syntax/test_rules.py`, `tests/test_run_lint.py`, `tests/test_rule_registration.py` | Intentionally broad; treats all latch-oriented procedural blocks as undesirable rather than trying to infer whether a latch was intentional. |
| `case generate` usage | `NO_CASE_GENERATE` | `Both` | `node` | Flags `case ... endcase` generate constructs. | `src/pkg/rules/syntax/no_case_generate.py` | `tests/rules/syntax/test_rules.py`, `tests/test_run_lint.py`, `tests/test_rule_registration.py` | Intentionally broad; treats `case generate` as a readability / structure smell rather than trying to infer whether it was the best structural choice. |
| Internal `inout` declaration | `NO_INOUT_INTERNAL` | `Both` | `node` | Flags internal module-body `inout` declarations. | `src/pkg/rules/syntax/no_inout_internal.py` | `tests/rules/syntax/test_rules.py`, `tests/test_run_lint.py` | First pass only targets internal `PortDeclarationSyntax` cases and intentionally does not cover ANSI module port declarations or interface-oriented edge cases. |

## Symbol Rules

These run after the walk against the accumulated symbol table for the linted file set.

| Rule | Code | Language Scope | Covers | Implemented By | Tests | Known Limitations |
|---|---|---|---|---|---|---|
| Unused variable | `UNUSED_VARIABLE` | `Both` | Flags declared variables that are never used. | `src/pkg/rules/symbol/unused_variable_rule.py` | `tests/rules/symbol/test_unused_variable_rule.py` | Only checks symbols whose `kind` is `"variable"`. |
| Read before write | `READ_BEFORE_WRITE` | `Both` | Flags variables that are read before they have any recorded write. | `src/pkg/rules/symbol/read_before_write_rule.py` | `tests/rules/symbol/test_read_before_write_rule.py` | Now treats compound assignments and increment/decrement forms as read+write events, but broader write-like contexts may still need richer access-mode modeling over time. |
| Implicit net | `NO_IMPLICIT_NET` | `Verilog` | Flags unresolved identifiers currently modeled as implicit nets. | `src/pkg/rules/symbol/no_implicit_net.py` | `tests/rules/symbol/test_no_implicit_net.py`, `tests/test_run_lint.py` | Now respects file-level ``default_nettype none`` handling, but the first pass still treats the directive as file-wide rather than modeling directive changes within a single file. |
| Multiple procedural drivers | `NO_MULTIPLE_DRIVERS` | `Both` | Flags declared variables written from more than one procedural block. | `src/pkg/rules/symbol/no_multiple_drivers.py` | `tests/rules/symbol/test_no_multiple_drivers.py`, `tests/test_run_lint.py` | First pass only tracks distinct procedural writers; declaration initializers and other non-procedural write contexts are intentionally ignored for now. |
| Undriven signal | `NO_UNDRIVEN_SIGNAL` | `Both` | Flags declared non-port variables that are read but never written. | `src/pkg/rules/symbol/no_undriven_signal.py` | `tests/rules/symbol/test_no_undriven_signal.py`, `tests/test_run_lint.py` | First pass excludes ports and implicit symbols, and does not yet try to model external drivers, continuous assignments, or more advanced net semantics. |
| Undeclared variable | `UNDECLARED_VARIABLE` | `Both` | Flags used-but-undeclared symbols that are not already modeled as implicit nets. | `src/pkg/rules/symbol/undeclared_variable.py` | `tests/rules/symbol/test_undeclared_variable.py` | This now covers ``default_nettype none`` cases in the first pass, but broader non-implicit undeclared-case modeling is still evolving. |
| Redeclared variable | `REDECLARED_VARIABLE` | `Both` | Flags symbols declared more than once in the same scope. | `src/pkg/rules/symbol/redeclared_variable.py` | `tests/rules/symbol/test_redeclared_variable.py` | Message reports the first declaration line but not currently richer scope context. |

## Module / Cross-File Rules

These run after all files have been walked and use batch-level module tracking.

| Rule | Code | Language Scope | Covers | Implemented By | Tests | Known Limitations |
|---|---|---|---|---|---|---|
| Duplicate module definition | `DUPLICATE_MODULE` | `Both` | Flags modules defined more than once across the linted file set. | `src/pkg/rules/module/duplicate_module_definition.py` | `tests/rules/module/test_duplicate_module_definition.py`, `tests/test_multi_file_lint.py` | Reports duplicates relative to the first-seen definition; current message is file-oriented rather than richer declaration-context-oriented. |
| Undefined module instantiation | `UNDEFINED_MODULE` | `Both` | Flags instantiations whose module type is not defined anywhere in the linted file set. | `src/pkg/rules/module/undefined_module.py` | `tests/rules/module/test_undefined_module.py` | Depends on the module-reference tracking captured during the walk; limited to what the current instantiation handler records. |

## Notes

- The README gives a short feature summary; this file is the more complete rule inventory.
- If a new rule is added, update this file in the same change so the rule list stays accurate.
