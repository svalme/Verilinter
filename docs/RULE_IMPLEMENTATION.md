# Rule Implementation Notes

This file is a contributor-facing guide to how rules are wired in Verilinter.

Use it alongside [RULES.md](RULES.md):

- `RULES.md` answers: "What rules exist and what do they cover?"
- `RULE_IMPLEMENTATION.md` answers: "What parts of the system usually need to change to implement a rule?"

## Rule Standards

These are the default standards for adding or changing a rule in this repo.
If a rule intentionally breaks one of them, document the reason in `RULES.md`
or in this file rather than leaving it implicit.

### Required wiring

Every new rule should, unless there is a documented exception:

- have a stable diagnostic `code`
- have a clear user-facing `message`
- be registered in the appropriate registry
- be listed in `RULES.md` in the same change
- include focused tests

### Rule folder organization

Rule files live under `src/pkg/rules/<category>/`, one folder per general RTL-lint
category (`combinational_logic`, `sequential_logic`, `clock_and_reset`, `latches`,
`conditional_and_case_statements`, `connectivity_and_hierarchy`,
`arrays_and_indexing`, `parameters_and_generate_logic`, `simulation_vs_synthesis`,
`unused_and_dead_code`, `naming_and_style`, `maintainability_and_complexity`,
`assertions_and_verification`, `declarations_and_types`, `width_and_signedness`,
`syntax_and_structure`, `operators_and_expressions`, `fsms` — plus
`race_conditions` and `security_and_safety` (currently deferred beyond MVP). Tests mirror this under `tests/rules/<category>/`.

This is a docs/discoverability grouping, not the implementation-shape split
described below (`Rule` vs `BaseSymbolRule`) and not the policy-metadata
`category` attribute on each rule class (see "Policy Category vs Implementation
Shape") — a rule's folder, base class, and `category` attribute are three
independent axes that happen to often correlate. The registries
(`rule_runner`/`symbol_rule_runner`/`module_rule_runner`, all at
`src/pkg/rules/`) don't care which folder a rule lives in; placement is purely
for humans browsing the tree. Pick the category folder whose name most closely matches what the rule actually catches.

Tests live under `tests/rules/<category>/`, mirroring the rule's own location
under `src/pkg/rules/<category>/`.

For syntax rules (subclassing `Rule`, registered with `rule_runner`), "focused
tests" usually means:

- unit coverage in `tests/rules/<category>/...`
- at least one lint-path test in `tests/test_run_lint.py`
- an overlap/regression test in `tests/test_rule_overlap_harness.py` when the rule
  could plausibly collide with another rule

For symbol or module rules (subclassing `BaseSymbolRule`, registered with
`symbol_rule_runner` or `module_rule_runner`), focused tests usually means:

- a dedicated rule test under `tests/rules/<category>/...`
- a lint-path or multi-file test when file attribution or cross-file behavior matters
- an overlap/regression test in `tests/test_rule_overlap_harness.py` when the rule
  could plausibly co-fire (or should suppress/be suppressed) alongside another rule
  on the same symbol or construct

`symbol_rule_runner`/`module_rule_runner` do no dedup or precedence resolution of
their own -- they just concatenate every selected rule's diagnostics (see
`src/pkg/rules/symbol_rule_runner.py`). Any "don't fire if a more specific rule
already covers this" behavior lives entirely in each rule's own conditions, so it
is only ever verified by a test that actually runs both rules together. When
adding a symbol/module rule, check whether an existing rule could match the same
symbol under some condition, and if so add a case to
`tests/test_rule_overlap_harness.py` pinning which rule should fire (see e.g.
`test_read_but_undriven_output_port_uses_output_specific_rule_not_unused_variable`
for the expected pattern).

When you add such a case, also record the relationship on both rule classes via
the `overlaps_with: tuple[str, ...]` class attribute (`BaseDiagnostic`, purely
declarative -- no runtime effect). `tests/test_rule_overlap_metadata.py` checks
every declared pair against a real registered code and against
`tests/test_rule_overlap_harness.py`, so a declared overlap can't silently lose
its regression test later. See `UnusedVariableRule`/`NoUndrivenOutputPortRule`/
`ReadBeforeWriteRule`/`NoWriteOnlyVariableRule`/`NoWriteOnlyInputPortRule`/
`NoInputPortWriteRule` for the existing worked example.

### Parser helper file organization

`src/pkg/parser/syntax_queries.py` is the stable public import surface for
every parser helper -- rules, handlers, and other parser code all import from
it (or from `syntax.py`, which re-exports the same names plus the `syntax_kinds`
constants it needs). It no longer defines helpers directly; it purely
re-exports them from `src/pkg/parser/_syntax_queries/`, split by theme:

- `shared.py`: low-level token/location/source-text plumbing, plus the
  leaf `identifier_name` accessor
- `access.py`: read/write access classification, `enclosing_*` ancestor walks
- `procedural.py`: procedural-block sensitivity-list and reset-style facts
- `shapes.py`: assignment target/RHS resolution and element-select (bit/part-select) decoding
- `declarators.py`: declarator name/initializer/kind/direction/dimension/width/signedness queries, plus clocking-declaration signal extraction
- `conditional_shapes.py`: `if`/`else`/case-branch shape predicates (begin/end wrapping, constant-condition detection, the `full_case`/`parallel_case` pragma check)
- `generate_blocks.py`: labeled/unlabeled generate-block and duplicate branch-label queries
- `instantiation.py`: instance/type names, port connections, and parameter overrides
- `real_number_conversions.py`: implicit real/fractional-time-literal-to-integral conversion checks
- `expressions.py`: AST-dispatch expression evaluation (`simple_expression_width_and_signed`, `natural_expression_width_and_signed`, unwrap parentheses)
- `literals.py`: literal/value/expression-kind checks (unsized literals, X/Z
  literals, width overflow, tri-state ternary detection)
- `node_kind_checks.py`: one-line "is this raw.kind == X" checks for banned
  SystemVerilog constructs (declarations, types, array dimensions)
- `structural_name_predicates.py`: identifier-exclusion predicates (is this
  name a module/type/callee/label reference rather than a variable read?) --
  the group `_STRUCTURAL_NAME_PREDICATES` in `identifier_name_handler.py` draws from
- `keywords_and_tokens.py`: keyword/operator token-kind checks (loop
  keywords, case/casex/casez, unique/priority, legacy net-type keywords)
- `package_scoping.py`: package imports, scoped package qualifiers, member selectors, and compilation unit package declaration queries
- `module_file.py`: file-scoped module-identity helpers, plus module-position
  and timescale-directive checks
- `system_tasks.py`: system task/function name-set checks
- `fsm.py`: structural state-machine model (`FsmModel`, `FsmTransition`, `state_machine_model`, `is_state_register_case`) with per-module procedural write summaries and per-case `Context.data` caching

Adding a new helper: put it in the submodule matching its theme (or a new one,
following `_syntax_queries/__init__.py`'s own guidance to split "when groups of
helpers can move without forcing repo-wide import churn"), then import it into
`syntax_queries.py`'s existing import block for that submodule and add it to
`syntax_queries.py`'s `__all__`. A submodule calling a helper that lives in
`syntax_queries.py` itself (i.e. in a *different* submodule) must use the same
lazy, function-body-scoped `from ..syntax_queries import name` pattern already
used throughout `access.py`/`procedural.py` -- a top-level import back into the
barrel module would be circular, since `syntax_queries.py` imports every
submodule at its own module-load time.

### Parser helper coding standards & style guidelines

All parser query helpers in `src/pkg/parser/_syntax_queries/` must adhere to the style and safety conventions defined in [CONTRIBUTING.md](CONTRIBUTING.md#code-style-for-parser-helpers--syntax-queries):

1. **Defensive Typing**:
   - The primary AST node parameter must be typed as `raw: object` (or `tree: object`) so that it can safely accept real CST nodes, test doubles (`FakeNode`), mock nodes, or `None`.
   - Predicates return `bool`.
   - Name/identifier extractors return `str | None` (empty strings normalize to `None`).
   - Single-node extractors return `SyntaxNode | None`.
   - Collections return `list[...]` or `set[...]` and **must return `[]` or `set()` (never `None`)** when missing or empty.

2. **Attribute Access via `getattr`**:
   - Inside `_syntax_queries/`, always use `getattr(raw, "field", None)` rather than raw dot-attribute access (`raw.field`) to guard against missing attributes on tokens or mismatched node kinds.
   - Never let an unhandled `AttributeError` escape from a query helper.

3. **Strict Isolation of `syntax_kinds`**:
   - Check CST kinds against constants imported from `..syntax_kinds` (e.g. `PACKAGE_DECLARATION_KIND`, `NAMED_PORT_CONNECTION_KIND`).
   - Never inspect kinds using string representations (`str(node.kind) == "..."` is banned).
   - Never import `syntax_kinds` or inspect `node.kind` outside `src/pkg/parser/`. External consumers (handlers, rules, engine) must always invoke a clean query helper predicate (enforced statically by `tests/meta/test_parser_boundary.py`).

4. **Consistent Naming Conventions**:
   - `is_*` / `has_*`: Boolean predicates (`is_empty_port_connection`, `has_default_case_item`).
   - `*_name`: String identifiers (`hierarchical_instance_name`, `instantiation_type_name`).
   - `*_list` / `*_items`: Node lists (`port_connection_list`, `case_statement_items`).
   - `iter_*`: Generators yielding nodes/pairs (`iter_identifier_reads`, `iter_assignment_nodes`).
   - `enclosing_*`: Ancestor-climbing context queries (`enclosing_procedural_block`, `enclosing_case_statement`).

5. **Cycle & Recursion Bounding (`traversal_guard`)**:
   - Recursive descents or walks must be wrapped with `@guarded_traversal(max_depth=..., default=...)` or `@guarded_generator(max_depth=...)` from `src.pkg.traversal_guard`.
   - Never use a flat, persistent visited set across calls due to PyBind11 C++ address recycling hazards.

### Layering standard

Put logic in the narrowest layer that can own it cleanly:

- parser helper:
  reusable syntax normalization or awkward `pyslang` shape access
- handler:
  traversal-time fact gathering that may be useful to more than one rule
- rule:
  the diagnostic decision itself

Do not put parser-shape knowledge directly into multiple rules if a shared parser
helper can express it once.

For complete system diagrams, AST query interactions, and dedicated expression/assignment
subsystem design, see [ARCHITECTURE.md](ARCHITECTURE.md).

If multiple rules or wrappers need the same raw node family, keep the family
definition in `src/pkg/parser/types.py` and expose any "is this one of those
nodes?" question through a parser helper such as `is_identifier_name_node(raw)`
instead of repeating `isinstance(..., (...))` tuples across non-parser files.

Do not add handler state for a fact that is only needed by one syntax rule if the
same fact can be derived statelessly from `vnode.raw` and `ctx.stack`.

Use `Context.data` only for cheap traversal-scoped memoization when a syntax fact
is still local to the current block/ancestor chain but would be too expensive to
recompute from scratch at every matching descendant node.

### Analysis standard: AST Dispatch over Regular Expressions

Do not use regular expressions over raw source text as the default mechanism for static analysis, expression evaluation, or shape matching. `pyslang` already parses Verilog and SystemVerilog into structured CST/AST nodes with precise `SyntaxKind` tags, tokens, and spans. String-based regexes break on comments, whitespace variations, line breaks, and nested syntax (such as parenthesized operations or slices within concatenations). Always inspect `vnode.raw` / `vnode.kind` or use query helpers in `src/pkg/parser/_syntax_queries/`. Regular expressions are reserved exclusively for simple lexical token checks (e.g. identifier naming conventions).

### Matching standard

Each rule should have a deliberate match shape:

- `token` when the policy is really about a specific keyword/operator
- `node` when the policy is about a whole construct
- `block` when the diagnostic should attach to a whole procedural/structural region

Choose the smallest anchor that still produces the right diagnostic location and
avoids accidental overlap.

If a rule is intentionally specific, prefer that over a broad umbrella rule.
Only add broad umbrella rules when overlapping diagnostics are an explicit policy
choice.

### Diagnostic standard

Diagnostics should be:

- stable in code
- understandable without reading the implementation
- anchored as close as practical to the construct being banned or diagnosed

If a rule needs a per-instance message, override `report()` or build the
diagnostic in `run()` rather than weakening the whole rule shape.

### Metadata standard

Policy-oriented rules should set:

- `category`
- `default_profiles`

Use the existing vocabulary unless there is a strong reason to extend it.
Current categories in use include:

- `classic_rtl_exclusion`
- `sv_subset`
- `rtl_subset`
- `rtl_correctness`
- `semantic_correctness`
- `module_correctness`
- `module_style`

Profile metadata is descriptive first. Do not add per-rule self-disabling logic;
selection should stay centralized in runner/config code.

Rules that can plausibly collide with another rule on the same symbol or
construct should also set:

- `overlaps_with`

Unlike `category`/`default_profiles`, this is conditional -- only set it when a
collision is actually plausible, not on every rule. It is a `tuple[str, ...]` of
other rule codes (declared on `BaseDiagnostic`), purely declarative with no
runtime effect: `symbol_rule_runner`/`module_rule_runner`/`rule_runner` still
just concatenate every rule's diagnostics, so any actual suppression or
co-firing behavior still lives in each rule's own `run()`/`applies()` logic.
Its only job is to be checked by `tests/test_rule_overlap_metadata.py` against
`tests/test_rule_overlap_harness.py`, so a known overlap can't silently lose its
regression test. See `UnusedVariableRule`/`NoUndrivenOutputPortRule`/
`ReadBeforeWriteRule`/`NoWriteOnlyVariableRule`/`NoWriteOnlyInputPortRule`/
`NoInputPortWriteRule` for the worked example, and the Testing standard section
above for when to add a case.

The internal named-profile mapping lives in `src/pkg/rules/profiles.py`. Use it
from code/tests that need a stable built-in profile name instead of hardcoding
those names in multiple places.

### Testing standard

New tests should try to protect against both false negatives and false positives.

That usually means checking:

- the intended construct does fire
- a nearby-but-different construct does not fire
- related rules still behave correctly when this one is present

If the rule fixes a subtle bug or architectural pitfall, add a regression test for
that exact shape.

### Documentation standard

When adding a rule, update the docs that answer these questions:

- `RULES.md`:
  what does the rule cover?
- `RULE_IMPLEMENTATION.md`:
  did this rule require a non-obvious implementation choice?

If the implementation was shaped by a pitfall, write down *why* it was built that
way, not just what files changed.

## Write Down *Why*, Not Just *What*

When a rule's design was shaped by a non-obvious pitfall, write that reasoning
down in one of the two places contributors will actually look:

- the rule's row in the Rule Shape Map below
- the rule's `Known Limitations` entry in `RULES.md`

The goal is to preserve implementation rationale, not project history.

## Mental Model

Most rules in this repo fall into one of two buckets:

1. Simple syntax rules
2. Shared-analysis / semantic rules

Simple syntax rules usually do **not** need handler changes.
They work because `pyslang` already exposes a distinct token or syntax node that
the rule can match directly.

Shared-analysis / semantic rules usually **do** need handler or symbol-model
changes. They work because the walker accumulates facts during traversal, and the
rule runs later over those facts.

## Rule Shape Map

| Rule | Category | Handler Changes? | Semantic / Model Changes? | Shared Analysis Used | Notes |
|---|---|---|---|---|---|
| `NO_CASEX_CASEZ` | Simple syntax | No | No | Raw token matching | Good example of a cheap token-level rule. |
| `NO_DEFPARAM` | Simple syntax | No | No | Raw token matching | Keyword-only legacy rule. |
| `NO_FORCE_RELEASE` | Simple syntax | No | No | Raw token matching | Flags both `force` and `release`. |
| `NO_ASSIGN_DEASSIGN` | Simple syntax | No | No | Raw token matching, gated by `enclosing_continuous_assign(ctx)` | The policy is about procedural `assign` / `deassign`, not ordinary continuous `assign`. |
| `NO_WAND_WOR` | Simple syntax | No | No | Raw token matching | Flags both resolved-net keywords. |
| `NO_TRIREG` | Simple syntax | No | No | Raw token matching | Another legacy keyword rule. |
| `NO_ALWAYS_LATCH` | Simple syntax | No | No | Procedural block node matching | Cheap block-level syntax rule. |
| `NO_LATCH_IN_ALWAYS_COMB` | Syntax with helper logic | No new handler | No new semantic model | Parser-side block / conditional helpers | More logic than a keyword rule, but still syntax-driven. |
| `DEFAULT_CASE` | Simple syntax (flag-based) | No | No | `CaseGenerateHandler`'s `CASE_GENERATE` / `DEFAULT` flags | Good example of a rule built around traversal context rather than post-walk semantic facts. |
| `NO_DEFAULT_CASE_STATEMENT` | Syntax with helper logic | No new handler | No new semantic model | `enclosing_case_statement` ancestor walk, `has_default_case_item` | Uses the nearest enclosing case statement instead of a flag so nested case statements stay independent. |
| `READ_BEFORE_WRITE` | Shared-analysis / semantic | Yes | Yes | Identifier read/write access classification | Relies on traversal-time read / write recording, plus parser helpers for read+write cases like compound assignments. |
| `NO_IMPLICIT_NET` | Shared-analysis / semantic | Yes | Yes | Unresolved identifier classification | Depends on handler logic that decides whether an unresolved use becomes an implicit net. |
| `NO_MULTIPLE_DRIVERS` | Shared-analysis / semantic | Yes | Yes | Procedural + continuous-assign driver identity tracking | Needs write events tied to an enclosing driver site. |
| `NO_UNDRIVEN_SIGNAL` | Shared-analysis / semantic | Yes | Yes | Declaration/write/use accumulation | Needs declarations, reads, writes, and port-vs-internal distinctions to be tracked consistently. |
| `NO_UNDRIVEN_OUTPUT_PORT` | Shared-analysis / semantic | Yes | Yes | Declaration/write/use accumulation, plus port direction classification | Uses shared port-direction data rather than re-deriving it in the rule. |
| `NO_WRITE_ONLY_INPUT_PORT` | Shared-analysis / semantic | No (reused) | No (reused) | Declaration/write/use accumulation, plus `Symbol.port_direction` | Good example of a second consumer of an existing shared fact. |
| `CIRCULAR_MODULE_INSTANTIATION` | Shared-analysis / semantic, cross-file | Yes | Yes | `SymbolTable.instantiation_edges` | Needs explicit module-to-module edge tracking, not just flat reference collection. |
| `NO_INCOMPLETE_SENSITIVITY_LIST` | Syntax with helper logic and handler caching | Yes | No | `procedural_block_sensitivity_names`, `iter_identifier_reads`, cached in `Context.data` | The fact is syntax-local, but caching it once per procedural block avoids repeated subtree walks. |
| `NO_MIXED_ASSIGNMENT_STYLE` | Syntax with helper logic and handler caching | Yes | No | `mixed_assignment_trigger_node`, cached in `Context.data` | Same caching shape as `NO_INCOMPLETE_SENSITIVITY_LIST`: syntax-local fact, computed once per block. |
| `NO_GATE_PRIMITIVE` | Simple syntax (token-based, context-gated) | No | No | Token matching plus `enclosing_primitive_instantiation(ctx)` | Keyword tokens such as `or` need positive gating so non-primitive contexts are not misclassified. |
| `NO_DELAY_CONTROL` | Simple syntax | No | No | Raw node-kind matching | Covers classic `#delay` forms without broadening into unrelated timing-control constructs. |
| `NO_PRIMITIVE_DECLARATION` / `UNDEFINED_MODULE` | Shared-analysis / semantic | Yes | Yes | `SymbolTable.primitives` | UDP declarations and UDP instances need shared tracking so they are not misread as undefined modules. |
| `NO_DISPLAY_SYSTEM_TASK` / `NO_SIMULATION_CONTROL_TASK` | Simple syntax (text-based) | No | No | System-task name text matching | These match by system-task name text because the AST kind is too generic on its own. |
| `NO_BIND_DIRECTIVE` / `IdentifierNameHandler` | Shared-analysis / semantic | No new handler | No new model, targeted predicate | `is_bind_directive_target` | Structural names inside syntax that looks like an identifier reference may need to be excluded before implicit-net creation. |
| Structural-name exclusions in `IdentifierNameHandler` | Shared-analysis / semantic | No new handler | No new model, targeted predicates | `is_bind_directive_target`, `is_subroutine_prototype_name`, `is_defparam_target`, `is_disable_statement_target`, `is_named_type_reference`, `is_invocation_callee`, `is_cover_cross_item`, `is_extends_clause_base_name` | Keep this pattern centralized so parser-shape exceptions do not sprawl across many rules. |
| `NO_DISABLE_STATEMENT` / `NO_EVENT_TRIGGER` | Simple syntax (token-based, context-gated) | No | No | Ancestor-based gating in parser helpers | Good examples of a token rule that still needs context to distinguish nearby grammar forms. |
| `NO_UNSIZED_LITERAL` | Simple syntax | No | No | `.parent`/`.right` check against `SIMPLE_ASSIGNMENT_KINDS`, plus a `ForLoopStatement` parent exclusion | No ancestor-stack walk needed at all -- a direct one-level-up `.parent` check on `vnode.raw` is enough, since pyslang parents an assignment's RHS literal directly. |
| `NO_IF_WITHOUT_BEGIN_END` / `NO_ELSE_WITHOUT_BEGIN_END` | Syntax with helper logic | No | No | `is_unwrapped_if_body`/`is_unwrapped_else_body` in `src/pkg/parser/syntax_queries.py` | One user-facing policy ("wrap every if/else branch") is split into two codes, following the repo's precedent of precise, separate codes (e.g. `DEFAULT_CASE`/`NO_DEFAULT_CASE_STATEMENT`) over one code shared across two `Rule` classes. |
| `MISSING_TIMESCALE_DIRECTIVE` | Syntax with helper logic (file-scoped, text-scan) | No | No | `is_first_module_declaration_in_file`/`has_timescale_directive_before` in `src/pkg/parser/syntax_queries.py`, same text-scan precedent as `has_full_parallel_case_pragma` | The only rule anchored on absence rather than presence. `SyntaxTree.root` is the bare `ModuleDeclarationSyntax` itself (no wrapper) for a single-top-level-construct file, and only becomes `CompilationUnitSyntax` with a `.members` list once there are two or more; handling only one shape would silently miss every single-module file. |
| `NO_MIXED_RESET_STYLE` | Shared-analysis / semantic | Yes | Yes | `SymbolTable.reset_style_events`, `classify_reset_style` in `src/pkg/parser/syntax_queries.py` | `ProceduralBlockHandler` needs `enclosing_module_scope`, a shared function on `src/pkg/semantic/scope.py` (the same "second consumer of an existing shared fact" shape documented for `NO_WRITE_ONLY_INPUT_PORT`). `is_posedge_event`/`is_negedge_event` strip token text before comparing, because the second signal in an `or`-joined sensitivity list carries leading trivia and would otherwise be misclassified, which this rule's exact per-signal edge count depends on. |
| `COMBINATIONAL_LOOP` | Shared-analysis / semantic | Yes | Yes | `SymbolTable.combinational_driver_ids`, DFS cycle detection mirroring `CIRCULAR_MODULE_INSTANTIATION` one level down (signals instead of modules) | `IdentifierNameHandler` computes `driver_id` for every access, reads included, not only writes. `NO_MULTIPLE_DRIVERS`, the only other `driver_id` consumer, filters to write events before reading it, and a dedicated regression test (`tests/rules/combinational_logic/test_no_multiple_drivers.py`) covers this because `IdentifierNameHandler` is the most heavily depended-on handler in the codebase. |
| `INSTANCE_OUTPUT_DRIVER_CONFLICT` | Shared-analysis / semantic, cross-file | No new handler | No new model (reuses `Symbol.is_written`) | `instance_output_driver_conflicts` in `src/pkg/rules/connection_analysis.py`, mirroring `unread_instance_output_details` | Port-connection expressions are never walked: `HierarchyInstantiationHandler` does not override `children()`, so a connected signal's `Symbol` gets no `UseEvent` from the connection itself. The rule therefore reads connections through the small `connection_analysis.py` helper rather than through `IdentifierNameHandler`/`identifier_access_modes`. |
| `MULTIPLE_INSTANCE_DRIVER_CONFLICT` | Shared-analysis / semantic, cross-file | No new handler | No new model | `multiple_instance_driver_conflicts` in `src/pkg/rules/connection_analysis.py`, reusing `bound_port_pairs` (same building block as its sibling) | Because port-connection expressions are never walked (see `INSTANCE_OUTPUT_DRIVER_CONFLICT`), two instances driving one net through their own output ports leave no `UseEvent` and no `Symbol.is_written` signal on either side, so there is no write-state fact to reuse. The rule groups `symbol_table.instantiations` by `parent_module`, then by connected signal name, using dict identity (`is`) to tell distinct instantiations apart. One instance binding two of its own output ports to the same net (`u1(.out1(x), .out2(x))`) is deliberately not flagged: that is a different bug shape than two instances colliding. |
| `MISSING_GENERATE_BLOCK_LABEL` | Simple syntax | No | No | `is_unlabeled_generate_block` in `src/pkg/parser/syntax_queries.py`, matching `SyntaxKind.GenerateBlock` plus `beginName is None` | No context-gating is needed: `GenerateBlockSyntax` is a distinct node kind pyslang uses only for a generate branch's `begin...end` body, so a direct kind check is unambiguous with no ancestor-stack walk (same shape as `NO_UNSIZED_LITERAL`'s one-level-up check). `default_profiles` excludes `rtl_strict`/`sv_rtl_subset`, since `NO_IF_GENERATE`/`NO_GENERATE_FOR`/`NO_CASE_GENERATE` already ban generate constructs entirely there; only `legacy_verilog` permits generate blocks, so only there is a labeling-style rule meaningful. The `beginName` field holds the `NamedBlockClauseSyntax`; `label` is always `None` at the syntax layer and is not the field to check. |
| `ONE_MODULE_PER_FILE` | Simple syntax (file-scoped) | No | No | `is_extra_module_declaration_in_file` in `src/pkg/parser/_syntax_queries/shapes.py`, reusing `is_module_declaration_node` and the same `CompilationUnitSyntax`-or-bare-root shape `is_first_module_declaration_in_file`/`MISSING_TIMESCALE_DIRECTIVE` already established | Built as the mirror image of `is_first_module_declaration_in_file`: walks `root.members` once, skips the first `ModuleDeclaration`-kind member, then flags every later one by identity (`member is raw`). A bare (unwrapped) `SyntaxTree.root` means the file has exactly one top-level construct, so it can never contain a second module and short-circuits to `False` (the same pyslang quirk documented on the `MISSING_TIMESCALE_DIRECTIVE` row). Counts `ModuleDeclaration`-kind members only, so a `package`/`interface`/etc. sharing a file with exactly one module does not trigger a false positive. |
| `EXPLICIT_XZ_LITERAL` | Simple syntax | No | No | Kind check on `UnbasedUnsizedLiteralExpression`/`IntegerVectorExpression`, reading `.literal`/`.value` directly | Reads the same two `SyntaxKind`s as `LITERAL_WIDTH_OVERFLOW`; the two rules never double-fire since `sized_literal_overflow` already excludes any value containing `x`/`z`/`?`. The attribute name differs by kind: `.literal` on the unbased-unsized form, `.value` on the sized form. |
| `XZ_EQUALITY_COMPARISON` | Simple syntax | No | No | Kind check on `EqualityExpression`/`InequalityExpression`, reusing `is_explicit_xz_literal` | Lives in the `operators_and_expressions` folder. `===`/`!==`/`==?`/`!=?` are separate `SyntaxKind`s (`CaseEqualityExpression`/`CaseInequalityExpression`/`WildcardEqualityExpression`/`WildcardInequalityExpression`) from plain `==`/`!=`, so no operator-token text matching is needed, just the node kind. |
| `CASEX_CASEZ_WILDCARD_CASE_ITEM` | Syntax with helper logic | No | No | `case_statement_items`/`case_item_expressions` (existing), `CaseStatementSyntax.caseKeyword` | Anchors at the `CaseStatement` node itself, the same shape as `NO_DUPLICATE_CASE_ITEM` in the same folder, rather than at individual case-item nodes. `x` is a wildcard character in `casex` but not in `casez` (only `z`/`?` are), so an all-`x` `casez` item (which does not match everything) is deliberately not classified like an all-`x` `casex` item (which does). `default_profiles` is `("legacy_verilog",)` only, since `NO_CASEX_CASEZ` already excludes both keywords under `rtl_strict`/`sv_rtl_subset` (the same reasoning as `MISSING_GENERATE_BLOCK_LABEL`). |
| `ASYNC_RESET_XZ_VALUE` | Syntax with helper logic | No new handler | No new semantic model | `async_reset_signal_names` (new, `_syntax_queries/procedural.py`), `is_within_async_reset_conditional` (new, `_syntax_queries/access.py`), `enclosing_procedural_block`, `is_conditional_statement`, `is_explicit_xz_literal` | Async-reset only: a sync-reset block's reset signal never appears in the sensitivity list, so it has no structural marker distinguishing it from any other identifier, and guessing would risk false positives and negatives on ordinary data-path `if`s. It does not disambiguate the reset-asserted branch from the other one (avoiding assumptions about `if(rst)` vs `if(!rst_n)` vs `if(rst_n==0)` polarity); one visible consequence is that an `else if` chain's inner conditional is still "inside" the outer reset-testing conditional, so a data-path branch reached via `else if` after `if (rst) ...` can still fire -- only a fully separate sibling `if` is guaranteed excluded. Declares `overlaps_with = ("EXPLICIT_XZ_LITERAL",)` since it always co-fires with that rule (the literal is flagged everywhere already), and a regression test pins this per the Testing standard above. |
| `UNDRIVEN_TRISTATE_SIGNAL` | Shared-analysis / semantic | Yes | Yes | `is_tristate_continuous_assign` (new, `syntax_queries.py`), `SymbolTable.tristate_driver_ids`/`mark_tristate_driver` (new, mirrors `combinational_driver_ids`/`mark_combinational_driver` exactly), `signal_names_connected_to_instances` (new, `connection_analysis.py`) | `IdentifierNameHandler` already computes `driver_id` for every write to a continuous-assign target, so this needed one additive `if` branch beside the existing `mark_combinational_driver` call. It touches no existing field or behavior, but because this is the most heavily depended-on handler in the codebase the full suite should be run after changing it (same caution as `COMBINATIONAL_LOOP`). "Purely internal" cannot be derived from `Symbol` state: a signal wired to an instance's port connection carries no `UseEvent` from that connection (`IdentifierNameHandler` never walks `.connections`, as documented on `INSTANCE_OUTPUT_DRIVER_CONFLICT`), so `signal_names_connected_to_instances` reads `symbol_table.instantiations`' `expr_name` fields directly, the same fields `multiple_instance_driver_conflicts` reads for its by-signal-name grouping. Requires exactly one driver (`NO_MULTIPLE_DRIVERS` owns the 2+-driver case regardless of tri-state intent) and a fully-`z` ternary branch (reusing `_is_all_wildcard_text` from `CASEX_CASEZ_WILDCARD_CASE_ITEM`, restricted to `"z"`; an `x`-else branch is `EXPLICIT_XZ_LITERAL`'s concern). No `overlaps_with` is declared: the rule is mutually exclusive by construction with `NO_UNDRIVEN_SIGNAL` (requires `is_written`) and `NO_MULTIPLE_DRIVERS` (requires exactly one driver), so ordinary "does not fire on a nearby case" unit tests in the rule's own file cover it. |
| `MODULE_FILENAME_MISMATCH` | Simple syntax (file-scoped), reads existing semantic state | No new handler | No new model | `is_module_filename_mismatch` in `src/pkg/parser/_syntax_queries/module_file.py` (composed from `module_declaration_names_in_file` and `module_declaration_file_stem`), fed by `enclosing_module_scope(ctx.scope()).file` in `src/pkg/semantic/scope.py` | Anchored on `is_first_module_declaration_in_file` (fires at most once per file, the same shape as `MISSING_TIMESCALE_DIRECTIVE`) and gathers every module name in the file via a second pass over `root.members` before deciding, since a multi-module file needs only one module to match the filename; this cannot be a single-node check like `ONE_MODULE_PER_FILE`. The file path comes from `enclosing_module_scope(ctx.scope()).file`, not from `tree.sourceManager.getFileName(...)`: pyslang reports the fixed placeholder `"source"` for every `SyntaxTree.fromText(...)` tree regardless of the logical filename the multi-file inline harness assigns via `symbol_table.set_current_file(file_name)`. `ModuleDeclarationHandler.update_context` calls `symbol_table.new_scope(...)`, which stamps `scope.file = symbol_table.current_file`, and the walker pushes that module scope onto `ctx` before `on_node`/`rule_runner.check` fires for the module-declaration vnode (`Walker._walk`: `update_context`, then `on_node`). So `ctx.scope()` inside `applies()` is the module's own scope and returns the correct file in both production and the test harness, with no handler changes. Inline-harness fixtures whose module name does not match their filename (e.g. `module top;` inside `"case_generate.sv"` in `tests/test_rule_overlap_harness.py`) also report this code and list it in their `expect_codes`. |

## Where To Change Things

When adding a rule, the common touchpoints are:

- `src/pkg/rules/...`
  Add the rule itself.
- `src/pkg/rules/register_rules.py`
  Register the rule so it actually runs.
- `RULES.md`
  Add the catalog entry in the same change.
- `tests/...`
  Add focused unit tests and at least one lint-path test when appropriate.

Then, depending on the rule type:

### If it is a simple syntax rule

Usually you only need:

- a parser helper in `src/pkg/parser/syntax_queries.py` or a token-kind set in `src/pkg/parser/syntax_kinds.py`
- the rule file
- registration
- tests

You usually do **not** need to touch handlers.

### If it is a shared-analysis / semantic rule

You may also need:

- a handler update under `src/pkg/handlers/`
- a symbol / scope / symbol-table update under `src/pkg/semantic/`
- a parser helper if access classification or parser-shape normalization is shared

The key question is:

"Does this rule only need to recognize syntax, or does it need facts accumulated during traversal?"

If it needs accumulated facts, it probably belongs in the shared-analysis bucket.

## Handler vs Parser Helper vs Rule

Use this split:

- Parser helper:
  Normalize awkward `pyslang` shape or expose reusable syntax facts.
- Handler:
  Observe traversal events and record shared semantic facts.
- Rule:
  Decide whether to emit a diagnostic from already-available syntax or semantic facts.

If rule logic starts duplicating parser-shape digging, move that shape knowledge into a parser helper.
If multiple rules need the same traversal-time fact, move that fact gathering into a handler or semantic model.
If generic vnode behavior needs parser-specific child, snippet, or location access,
prefer a small parser helper over embedding those raw field paths directly in
`vnodes/`.

## Good Contributor Heuristic

Before editing a handler, ask:

"Could this rule be implemented cleanly by matching an existing token or syntax node?"

If yes, prefer the simpler syntax-rule route.

Before adding rule-specific state to a handler, ask:

"Is this really a shared fact that more than one rule may want?"

If yes, it is probably a semantic-model or shared-analysis addition, not just a one-off rule hack.

If the fact is still syntax-local but expensive to recompute repeatedly inside one
block, prefer parser helpers plus `Context.data` over pushing it into the semantic
model.

## Policy Category vs Implementation Shape

Implementation shape and policy category are different axes.

- Implementation shape answers "how does this rule work technically?"
- Policy category answers "what kind of restriction is this rule expressing?"

Example:

- `NO_PACKAGE_DECLARATION` is a simple syntax rule and an `sv_subset` policy rule.
- `NO_DEFPARAM` is a simple syntax rule and a `classic_rtl_exclusion` policy rule.

That distinction matters because rule selection should key off policy metadata
without forcing a file or folder reorganization first.

## Assignment, Driver, and Branch Coverage Matrices

For a rule that consumes value transfers, audit every applicable syntax form.
Use the shared assignment target/RHS resolver and expression queries; do not
reimplement source-text parsing inside the rule.

| Vehicle | Width/sign/truncation | Literal policy | Self-assignment |
|---|---|---|---|
| Continuous `assign` | Check | Check | Check simple identifiers |
| Blocking `=` | Check | Check | Check simple identifiers |
| Nonblocking `<=` | Check | Check | Check simple identifiers |
| Variable/net initializer | Check | Check | Excluded: initialization differs from redundant assignment |
| Port default | Check | Check | Excluded |
| Compound assignment | Excluded from plain transfer rules; needs operation semantics | Literal overflow still applies; unsized policy excluded | Excluded |

Parameter initializers are excluded from ordinary assignment width and unsized
assignment-literal policy. Literal overflow is lexical and applies wherever
an unsigned sized literal occurs. Test sliced/indexed and concatenated targets,
known and unknown operands, both HDL dialects, and explicit cast boundaries.

| Driver source | Audit requirement |
|---|---|
| Continuous / procedural / initializer | Preserve driver identity and read/write distinctions |
| Instance output / subroutine output, inout, ref | Preserve direction and actual-target selectors |
| Generate alternatives | Preserve branch exclusivity across serialization |

| Branch shape | Audit requirement |
|---|---|
| If/else and case | Check asymmetric assignments to multiple variables |
| Nested conditional ladders | Check omitted intermediate branches and empty statements |
| Pre-assignment and loops | Preserve statement order within a block; avoid imposing order across concurrent blocks |

FSM rules should consume `state_machine_model` instead of independently
guessing a state/next-state relationship. `ModuleDeclarationHandler` attaches a
per-module `module_cache` on `Context.data` (read and written only through `node_cache_get`/`node_cache_put`; see `CONTRIBUTING.md`, "Memoizing Results Per Syntax Node"), and `CaseStatementHandler`
computes `FsmModel` once per `CaseStatementNode` (attaching it to
`ctx.data["fsm_model"]` and `module_scope.fsm_models`) so all FSM rules share a
single evaluation without re-walking `module.members`. Its transitions are
structural: unknown destinations and conditional guards require further
analysis before issuing reachability or trap-state diagnostics.
