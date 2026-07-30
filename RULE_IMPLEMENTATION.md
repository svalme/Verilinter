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

Do not add handler state for a fact that is only needed by one syntax rule if the
 same fact can be derived statelessly from `vnode.raw` and `ctx.stack`.

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

Profile metadata is descriptive first. Do not add per-rule self-disabling logic;
selection should stay centralized in runner/config code.

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
They work because `pyslang` already exposes a distinct token or syntax node that the rule can match directly.

Shared-analysis / semantic rules usually **do** need handler or symbol-model changes.
They work because the walker accumulates facts during traversal, and the rule runs later over those facts.

## Rule Shape Map

| Rule | Category | Handler Changes? | Semantic / Model Changes? | Shared Analysis Used | Notes |
|---|---|---|---|---|---|
| `NO_CASEX_CASEZ` | Simple syntax | No | No | Raw token matching | Good example of a cheap token-level rule. |
| `NO_DEFPARAM` | Simple syntax | No | No | Raw token matching | Keyword-only legacy rule. |
| `NO_FORCE_RELEASE` | Simple syntax | No | No | Raw token matching | Flags both `force` and `release`. |
| `NO_ASSIGN_DEASSIGN` | Simple syntax | No | No | Raw token matching | Flags both procedural `assign` and `deassign`. |
| `NO_WAND_WOR` | Simple syntax | No | No | Raw token matching | Flags both resolved-net keywords. |
| `NO_TRIREG` | Simple syntax | No | No | Raw token matching | Another legacy keyword rule. |
| `NO_ALWAYS_LATCH` | Simple syntax | No | No | Procedural block node matching | Cheap block-level syntax rule. |
| `NO_LATCH_IN_ALWAYS_COMB` | Syntax with helper logic | No new handler | No new semantic model | Parser-side block / conditional helpers | More logic than a keyword rule, but still syntax-driven. |
| `DEFAULT_CASE` | Simple syntax (flag-based) | No | No | `CaseGenerateHandler`'s `CASE_GENERATE` / `DEFAULT` flags | Good example of a rule built around traversal context rather than post-walk semantic facts. |
| `NO_DEFAULT_CASE_STATEMENT` | Syntax with helper logic | No new handler | No new semantic model | `enclosing_case_statement` ancestor walk (`ctx.stack`), `has_default_case_item` | Deliberately *not* a `ContextFlag`-based design like `DEFAULT_CASE` (case generate's sibling rule, directly above) for the reason described there: Context flags accumulate downward and never clear, so a nested case statement would inherit an outer case's `DEFAULT` flag even with no default of its own — a false negative for the single most common shape this rule needs to handle correctly (nested case statements). Resolving the *nearest* enclosing `CaseStatementSyntax` fresh per `endcase` token sidesteps that entirely, at the cost of walking `ctx.stack` once per `endcase` rather than reading a flag. |
| `READ_BEFORE_WRITE` | Shared-analysis / semantic | Yes | Yes | Identifier read/write access classification | Relies on traversal-time read / write recording, plus parser helpers for read+write cases like compound assignments. |
| `NO_IMPLICIT_NET` | Shared-analysis / semantic | Yes | Yes | Unresolved identifier classification | Depends on handler logic that decides whether an unresolved use becomes an implicit net. |
| `NO_MULTIPLE_DRIVERS` | Shared-analysis / semantic | Yes | Yes | Procedural + continuous-assign driver identity tracking | Needs write events tied to an enclosing driver site. |
| `NO_UNDRIVEN_SIGNAL` | Shared-analysis / semantic | Yes | Yes | Declaration/write/use accumulation | Needs declarations, reads, writes, and port-vs-internal distinctions to be tracked consistently. |
| `NO_UNDRIVEN_OUTPUT_PORT` | Shared-analysis / semantic | Yes | Yes | Declaration/write/use accumulation, plus port direction classification | Same read/write facts as `NO_UNDRIVEN_SIGNAL`, filtered to the port case that rule excludes. Needed a new shared fact, `Symbol.port_direction`, since the existing `is_port` bool couldn't distinguish `output` from `input`/`inout`/`ref`. That fact is gathered once in `DeclaratorHandler` via `declarator_port_direction` (mirrors the existing `declarator_is_port` ancestor walk) so any future port-direction-aware rule can reuse it without re-deriving it from the AST. |
| `NO_WRITE_ONLY_INPUT_PORT` | Shared-analysis / semantic | No (reused) | No (reused) | Declaration/write/use accumulation, plus `Symbol.port_direction` | Pure rule-side addition once `NO_UNDRIVEN_OUTPUT_PORT` had already introduced `port_direction` — no handler or semantic-model changes were needed for this one, just a second consumer of the same shared fact. Good example of the payoff of putting a fact in the shared model instead of a one-off rule hack. |
| `CIRCULAR_MODULE_INSTANTIATION` | Shared-analysis / semantic, cross-file | Yes | Yes | `SymbolTable.instantiation_edges` | Needs explicit module-to-module edge tracking, not just flat reference collection. |
| `NO_INCOMPLETE_SENSITIVITY_LIST` | Syntax with helper logic and handler caching | Yes | No | `procedural_block_sensitivity_names`, `iter_identifier_reads`, cached in `Context.data` | The fact is syntax-local, but caching it once per procedural block avoids repeated subtree walks. |
| `NO_GATE_PRIMITIVE` | Simple syntax (token-based) | No | No | Raw token matching (`GATE_PRIMITIVE_TOKEN_KINDS`) | Deliberately matches the gate *keyword token* (`and`/`or`/`nand`/.../`notif1`) rather than the wrapping `PrimitiveInstantiationSyntax` node, mirroring this repo's existing `NO_TRAN_RTRAN`/`NO_TRANIF_RTRANIF` precedent (`tran`/`rtran` are themselves gate-primitive keywords parsed inside the same node kind, and both were already built as token checks). **Known blind spot, by design, not an oversight**: an instance of a user-declared `primitive` (UDP, see `NO_PRIMITIVE_DECLARATION`) parses as an ordinary `HierarchyInstantiationSyntax` — syntactically indistinguishable from a normal module instantiation without resolving the instantiated type name against known UDP declarations. Only built-in gate keywords are catchable this way; a UDP-instance-aware version would need to become a shared-analysis rule (module-reference resolution, like `UNDEFINED_MODULE`) instead of a token check. Not built that way now because it would be new machinery for a rare case (behavioral RTL rarely instantiates UDPs directly). |
| `NO_DELAY_CONTROL` | Simple syntax | No | No | Raw node-kind matching (`DELAY_CONTROL_KINDS = {DelayControl, Delay3}`) | Covers `#5` (assignment/gate single-value delay) and `#(1,2,3)` (parenthesized multi-value gate delay) via two distinct pyslang node kinds. Deliberately does *not* include cycle delays (`##N`, `SyntaxKind.CycleDelay`) or one-step/event controls (`@`) — those are different timing-control concepts (clocking-block relative delay, event sensitivity) rather than the classic non-synthesizable `#delay` this rule targets; folding them in would make one rule do the job of several more specific ones, the same reasoning `RULES.md`'s Notes section gives for preferring precise rules over broad umbrellas. |
| `NO_DISPLAY_SYSTEM_TASK` / `NO_SIMULATION_CONTROL_TASK` | Simple syntax (text-based, new matching mechanism) | No | No | Token-**text** matching (`system_task_name`, comparing `.systemIdentifier.valueText` against a name set) — not `SyntaxKind`/`TokenKind` identity | Every other rule in this codebase matches on `SyntaxKind`/`TokenKind` enum identity because pyslang gives each construct a distinct kind. System tasks/functions (`$display`, `$finish`, etc.) don't get that treatment — they all parse as one `SystemNameSyntax` node (`SyntaxKind.SystemName`), whether called bare (`$finish;`) or via `InvocationExpressionSyntax` (`$display(...)`), and the actual task name is only available as the identifier token's text. Verified by parsing both forms directly with pyslang: `SystemNameSyntax` is visited as its own vnode by the walker either way, so the rule doesn't need to special-case the invoked-vs-bare distinction — it just checks `is_display_system_task`/`is_simulation_control_task` (`src/pkg/parser/syntax_queries.py`) against whichever vnode it's handed. Two separate rules/codes rather than one, since "print debug output" and "halt the simulator" are different policy concerns despite both being system tasks. |

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

## Good Contributor Heuristic

Before editing a handler, ask:

"Could this rule be implemented cleanly by matching an existing token or syntax node?"

If yes, prefer the simpler syntax-rule route.

Before adding rule-specific state to a handler, ask:

"Is this really a shared fact that more than one rule may want?"

If yes, it is probably a semantic-model or shared-analysis addition, not just a one-off rule hack.

## Policy Category vs Implementation Shape

Implementation shape and policy category are different axes.

- Implementation shape answers "how does this rule work technically?"
- Policy category answers "what kind of restriction is this rule expressing?"

Example:

- `NO_PACKAGE_DECLARATION` is a simple syntax rule and an `sv_subset` policy rule.
- `NO_DEFPARAM` is a simple syntax rule and a `classic_rtl_exclusion` policy rule.

That distinction matters because future configuration should key off policy metadata without forcing a file or
folder reorganization first.

