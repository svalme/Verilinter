# Contributing

This file is the coding-style reference for Verilinter.

Read alongside:

- [README.md](README.md) — what the project is, how to run it
- [RULES.md](RULES.md) — the rule catalog
- [RULE_IMPLEMENTATION.md](RULE_IMPLEMENTATION.md) — how rules are wired (handlers, parser helpers, shared facts)

## Type Annotations

**Every function and method signature must be fully annotated: every parameter, and the return type.**
This includes `self`-only helper methods with an obvious-looking body — `-> bool`, `-> None`, `-> str | None`
cost nothing to write and are what makes the codebase's type checker (Pylance/Pyright, run by most contributors'
editors) actually useful instead of silently skipping the function.

```python
# Not this:
def applies(self, vnode, ctx) -> bool:
    return is_always_latch_block(vnode.raw)

# This:
def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
    return is_always_latch_block(vnode.raw)
```

(A bare `vnode, ctx` in a syntax rule's `applies()` is a regression, not a model to copy.)

**Prefer the precise type that already exists over `dict[str, Any]` or `Any`.** If a `TypedDict` already
describes the shape you're handling — `UseEvent` and `Location` both exist for exactly this reason — use it.
Falling back to `dict[str, Any]` when a narrower type is already defined either hides a real bug from the type
checker or invites one: annotating a collection of `UseEvent` values as `dict[str, dict[str, Any]]` is a real type error, not a style nitpick: a `TypedDict`'s fixed key set isn't assignable to an open `dict[str, Any]`. Annotate it `dict[str, UseEvent]`.

Two annotation situations that come up often in this codebase:

- **Circular-import-only types**: several modules need `Context` for type hints but importing it directly would
  create an import cycle. The existing convention is `if TYPE_CHECKING: from ...walk.context import Context`,
  then annotating with the string form `ctx: "Context"`. Follow this rather than restructuring imports to avoid
  it.
- **`TypedDict` values with `NotRequired` keys**: don't subscript a `NotRequired` key directly (`event["driver_location"]`) — the type checker can't know from a dict lookup elsewhere that the key is actually present. Either use `.get(...)` and check for `None`, or — if you've already validated presence and need to keep using the value later — carry the validated value alongside the object explicitly (a tuple, a small local variable) rather than re-deriving it from an unsafe subscript. `NoMultipleDriversRule` does this: it captures `driver_location` once, right where it validates it's not `None`, and stores `(event, driver_location)` together instead of subscripting `event["driver_location"]` again later.

## Design Patterns

**The registry-plus-decorator pattern is how every extensible collection in this codebase works. New
collections of the same shape should follow it, not invent a new one.** Five things already use it:

| Registry | Decorator | Lookup / run method |
|---|---|---|
| `Dispatch` (`walk/dispatch.py`) | `@dispatch.register(NodeType)` | `Dispatch.get(vnode)` |
| `VNodeFactory` (`vnodes/vnode_factory.py`) | `@vnode_factory.register(...)` | `vnode_factory.create(...)` |
| `RuleRunner` (`rules/rule_runner.py`) | `@rule_runner.register` | `rule_runner.check(vnode, ctx)` / `.run(walk_results)` |
| `SymbolRuleRunner` (`rules/symbol_rule_runner.py`) | `@symbol_rule_runner.register` | `symbol_rule_runner.run(symbol_table)` |
| `ModuleRuleRunner` (`rules/module_rule_runner.py`) | `@module_rule_runner.register` | `module_rule_runner.run(symbol_table)` |

The shape: a single module-level instance, a `register` method used as a decorator so registration is a *side
effect of importing the module* (see `RULE_IMPLEMENTATION.md`'s Wiring Checklist for why every one of these
modules has to actually get imported somewhere for this to work), and a lookup/run method that the rest of the
codebase calls without needing to know what's registered. If you're adding something that's naturally a
collection of interchangeable, independently-registered things — not just these five — reach for this shape
before inventing a bespoke registration mechanism.

**Follow the parser / vnode / handler / rule layering already documented in `RULE_IMPLEMENTATION.md`.** That
file's "Handler vs Parser Helper vs Rule" section and "Layer Responsibilities" section are the authority on
where a given piece of logic belongs — this file doesn't repeat that split, just points at it.

**`BaseDiagnostic` is the shared base for both rule kinds (`Rule` and `BaseSymbolRule`).** It provides
`report(vnode) -> dict` using `self.code`/`self.message`. If a rule needs a dynamic, per-instance message
(the diagnostic needs to name a specific signal, line, etc. — most symbol/module rules do this by building the
`dict` by hand in `run()`), a syntax `Rule` can override `report()` rather than being forced into a static
`message` string; `NoIncompleteSensitivityListRule` does this. Don't invent a second diagnostic-shaping
mechanism alongside `BaseDiagnostic` for that case.

## Rule Policy Metadata

`BaseDiagnostic` also exposes lightweight policy metadata:

- `category`
- `default_profiles`

Right now these are descriptive only; they do not change runtime rule selection. Use them to record policy
intent, not to build per-rule behavior:

- `category` answers "what kind of restriction is this?" such as `classic_rtl_exclusion` or `sv_subset`.
- `default_profiles` answers "if built-in profiles are added later, which ones should include this rule by default?"

If profile selection is added later, it should happen centrally in config / runner code using this shared
metadata, not inside individual rule files.

A small internal built-in mapping lives in `src/pkg/rules/profiles.py`.
Use that for code/tests that need a named profile instead of hardcoding profile
strings in multiple places. The CLI still does not expose profile selection.

## Rule Checklist

When adding a rule, use this checklist by default:

- choose the right rule family:
  syntax, symbol, or module
- add a stable `code`
- add a clear `message`
- add `category` and `default_profiles` when the policy bucket is clear
- register the rule
- add focused tests (see `TESTING.md` for the kinds of tests that exist and
  where a new one belongs)
- update `RULES.md`
- document any non-obvious implementation reason in `RULE_IMPLEMENTATION.md`

Two quality checks matter especially here:

- avoid duplicating parser-shape logic across multiple rules when a helper can own it once
- add at least one "near miss" test so the rule proves what it does *not* flag, not just what it does flag

## CLI Change Checklist

When adding or changing a command-line option, use this checklist by default:

- define clear argument names, defaults, help text, and metavar values in the argument parser
- validate invalid or incompatible option combinations and return a useful non-zero exit code
- preserve existing behavior for invocations that do not use the new option
- add focused tests for the intended behavior, validation failures, and output or exit status when applicable
- update `CLI.md` with the option's purpose, requirements, and an example invocation
- update the relevant domain documentation when the option changes a workflow, lifecycle, storage format, or configuration behavior
- update `README.md` when the option is part of the primary user workflow or deserves a quick-start example

For options that perform maintenance or make destructive changes, document what data is affected, whether the
operation can be combined with other options, and any follow-up step needed to reclaim resources or restore state.
