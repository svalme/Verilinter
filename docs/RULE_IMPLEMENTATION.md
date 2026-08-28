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

For syntax rules, "focused tests" usually means:

- unit coverage in `tests/rules/syntax/...`
- at least one lint-path test in `tests/test_run_lint.py`
- an overlap/regression test when the rule could plausibly collide with another rule

For symbol or module rules, focused tests usually means:

- a dedicated rule test under `tests/rules/symbol/...` or `tests/rules/module/...`
- a lint-path or multi-file test when file attribution or cross-file behavior matters

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

If multiple rules or wrappers need the same raw node family, keep the family
definition in `src/pkg/parser/types.py` and expose any "is this one of those
nodes?" question through a parser helper such as `is_identifier_name_node(raw)`
instead of repeating `isinstance(..., (...))` tuples across non-parser files.

Do not add handler state for a fact that is only needed by one syntax rule if the
same fact can be derived statelessly from `vnode.raw` and `ctx.stack`.

Use `Context.data` only for cheap traversal-scoped memoization when a syntax fact
is still local to the current block/ancestor chain but would be too expensive to
recompute from scratch at every matching descendant node.

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
| `INSTANCE_OUTPUT_DRIVER_CONFLICT` | Shared-analysis / semantic, cross-file | No new handler | No new model (reuses `Symbol.is_written`) | `instance_output_driver_conflicts` in `src/pkg/rules/module/connection_analysis.py`, mirroring `unread_instance_output_details` | Port-connection expressions are never walked: `HierarchyInstantiationHandler` does not override `children()`, so a connected signal's `Symbol` gets no `UseEvent` from the connection itself. The rule therefore reads connections through the small `connection_analysis.py` helper rather than through `IdentifierNameHandler`/`identifier_access_modes`. |
| `MISSING_GENERATE_BLOCK_LABEL` | Simple syntax | No | No | `is_unlabeled_generate_block` in `src/pkg/parser/syntax_queries.py`, matching `SyntaxKind.GenerateBlock` plus `beginName is None` | No context-gating is needed: `GenerateBlockSyntax` is a distinct node kind pyslang uses only for a generate branch's `begin...end` body, so a direct kind check is unambiguous with no ancestor-stack walk (same shape as `NO_UNSIZED_LITERAL`'s one-level-up check). `default_profiles` excludes `rtl_strict`/`sv_rtl_subset`, since `NO_IF_GENERATE`/`NO_GENERATE_FOR`/`NO_CASE_GENERATE` already ban generate constructs entirely there; only `legacy_verilog` permits generate blocks, so only there is a labeling-style rule meaningful. The `beginName` field holds the `NamedBlockClauseSyntax`; `label` is always `None` at the syntax layer and is not the field to check. |

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
