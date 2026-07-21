# Rule Implementation Notes

This file is a contributor-facing guide to how rules are wired in Verilinter.

Use it alongside [RULES.md](RULES.md):

- `RULES.md` answers: "What rules exist and what do they cover?"
- `RULE_IMPLEMENTATION.md` answers: "What parts of the system usually need to change to implement a rule?"

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
| `READ_BEFORE_WRITE` | Shared-analysis / semantic | Yes | Yes | Identifier read/write access classification | Relies on traversal-time read / write recording, plus parser helpers for read+write cases like compound assignments. |
| `NO_IMPLICIT_NET` | Shared-analysis / semantic | Yes | Yes | Unresolved identifier classification | Depends on handler logic that decides whether an unresolved use becomes an implicit net. |
| `NO_MULTIPLE_DRIVERS` | Shared-analysis / semantic | Yes | Yes | Procedural + continuous-assign driver identity tracking | Needs write events tied to an enclosing driver site. |
| `NO_UNDRIVEN_SIGNAL` | Shared-analysis / semantic | Yes | Yes | Declaration/write/use accumulation | Needs declarations, reads, writes, and port-vs-internal distinctions to be tracked consistently. |

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
