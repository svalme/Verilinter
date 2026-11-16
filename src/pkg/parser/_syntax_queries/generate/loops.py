"""Which values of the enclosing generate loops reach a node, and under which of them it is elaborated.

A node inside `for (genvar i = 0; i < N; i++)` exists once per value of `i`; inside an `if` or `case`
generate it exists only for the values that select its branch. `generate_bindings` lists those values,
so an index such as `a[2*i+1]` can be read as the set of indices it takes."""
from __future__ import annotations

from types import SimpleNamespace

from ...syntax_kinds import (
    ADD_ASSIGNMENT_KIND,
    ASSIGNMENT_EXPRESSION_KIND,
    ELSE_CLAUSE_KIND,
    LOOP_GENERATE_KIND,
    POSTDECREMENT_EXPRESSION_KIND,
    POSTINCREMENT_EXPRESSION_KIND,
    PREDECREMENT_EXPRESSION_KIND,
    PREINCREMENT_EXPRESSION_KIND,
    SUBTRACT_ASSIGNMENT_KIND,
)
from ..expressions.constant_evaluation import evaluate_constant_expression, evaluate_constant_text_expression
from .blocks import loop_generate_genvar_name, taken_case_item
from ..node_kind_checks import is_case_generate_node, is_if_generate_node
from ..shared import identifier_name

_MAX_ITERATIONS = 256
_MAX_BINDINGS = 1024
_MAX_ANCESTORS = 128

Binding = dict[str, int]


class _BoundScope:
    """A scope that answers the bound names with their integer value and every other name from the wrapped scope.

    A parameter declared inside a loop body from the genvar (`localparam Cnt = i + BASE;`) has no value of its
    own where it is declared, so it is evaluated here from its initializer with the genvars bound."""

    def __init__(self, scope: object, values: Binding) -> None:
        self._scope = scope
        self._values = values
        self._resolving: set[str] = set()

    def lookup_package_member(self, package_name: str, name: str) -> object:
        lookup = getattr(self._scope, "lookup_package_member", None)
        return lookup(package_name, name) if callable(lookup) else None

    def lookup_hierarchical(self, name: str) -> object:
        if name in self._values:
            return SimpleNamespace(value=self._values[name])
        lookup = getattr(self._scope, "lookup_hierarchical", None)
        symbol = lookup(name) if callable(lookup) else getattr(self._scope, "lookup", lambda _n: None)(name)
        return self._with_bound_value(name, symbol)

    def _with_bound_value(self, name: str, symbol: object) -> object:
        """`symbol`, or a stand-in carrying its value when it is a parameter whose value depends on the bound genvars."""
        text = getattr(symbol, "initializer_text", None)
        if (
            symbol is None
            or getattr(symbol, "value", None) is not None
            or not text
            or getattr(getattr(symbol, "kind", None), "name", None) != "PARAMETER"
            or name in self._resolving
        ):
            return symbol
        self._resolving.add(name)
        try:
            value = evaluate_constant_text_expression(text, scope=self)
        finally:
            self._resolving.discard(name)
        return SimpleNamespace(value=value) if value is not None else symbol


def _evaluate(expr: object, scope: object, binding: Binding) -> int | None:
    return evaluate_constant_expression(expr, scope=_BoundScope(scope, binding) if binding else scope)


def _loop_variable(loop: object) -> str | None:
    """The loop's genvar: declared in the header (`genvar i`) or named by `identifier`."""
    declared = loop_generate_genvar_name(loop)
    if declared:
        return declared
    identifier = getattr(loop, "identifier", None)
    value = getattr(identifier, "value", None)
    return value if isinstance(value, str) and value else None


def _next_value(loop: object, name: str, current: int, scope: object, binding: Binding) -> int | None:
    """The genvar's value after one iteration, from the loop's step expression; None if it is not understood."""
    step = getattr(loop, "iterationExpr", None)
    kind = getattr(step, "kind", None)
    if kind in (POSTINCREMENT_EXPRESSION_KIND, PREINCREMENT_EXPRESSION_KIND):
        return current + 1
    if kind in (POSTDECREMENT_EXPRESSION_KIND, PREDECREMENT_EXPRESSION_KIND):
        return current - 1
    if kind in (ASSIGNMENT_EXPRESSION_KIND, ADD_ASSIGNMENT_KIND, SUBTRACT_ASSIGNMENT_KIND):
        if identifier_name(getattr(step, "left", None)) != name:
            return None
        inner = {**binding, name: current}
        right = _evaluate(getattr(step, "right", None), scope, inner)
        if right is None:
            return None
        if kind == ADD_ASSIGNMENT_KIND:
            return current + right
        if kind == SUBTRACT_ASSIGNMENT_KIND:
            return current - right
        return right
    return None


def loop_iteration_values(loop: object, scope: object, outer: Binding) -> list[int] | None:
    """The values the loop's genvar takes, in order, given the values of the genvars of the loops around
    it. None when the bounds are not constants, the step is not understood, or the loop runs past a cap."""
    name = _loop_variable(loop)
    if name is None:
        return None
    value = _evaluate(getattr(loop, "initialExpr", None), scope, outer)
    values: list[int] = []
    for _ in range(_MAX_ITERATIONS):
        if value is None:
            return None
        inner = {**outer, name: value}
        holds = _evaluate(getattr(loop, "stopExpr", None), scope, inner)
        if holds is None:
            return None
        if not holds:
            return values
        values.append(value)
        value = _next_value(loop, name, value, scope, outer)
    return None


def _branch_selected(parent: object, child: object, scope: object, binding: Binding) -> bool:
    """Whether the branch of the `if` or `case` generate `parent` that contains `child` is elaborated for
    `binding`. A condition that cannot be evaluated counts as selecting it."""
    if is_if_generate_node(parent):
        condition = _evaluate(getattr(parent, "condition", None), scope, binding)
        if condition is None:
            return True
        else_clause = getattr(parent, "elseClause", None)
        if child is getattr(parent, "block", None):
            return bool(condition)
        if else_clause is not None and child is else_clause:
            return not condition
        return True
    selected = taken_case_item(parent, _BoundScope(scope, binding) if binding else scope)
    return selected is None or selected is child


def generate_bindings(raw: object, scope: object) -> list[Binding] | None:
    """The values of the enclosing generate loops for which `raw` is elaborated, one binding (genvar name to
    value) per elaboration. `[{}]` when no loop encloses it and its branches are selected; `[]` when no
    value selects its branches (it never exists); None when more than a thousand elaborations would be
    needed. A loop whose bounds cannot be evaluated leaves its genvar out of the bindings, so an
    expression that uses it evaluates to unknown."""
    loops: list[object] = []
    conditionals: list[tuple[object, object]] = []
    child = raw
    for _ in range(_MAX_ANCESTORS):
        parent = getattr(child, "parent", None)
        if parent is None:
            break
        if getattr(parent, "kind", None) == LOOP_GENERATE_KIND:
            loops.append(parent)
        elif is_if_generate_node(parent) or is_case_generate_node(parent):
            conditionals.append((parent, child))
        child = parent

    bindings: list[Binding] = [{}]
    for loop in reversed(loops):
        extended: list[Binding] = []
        name = _loop_variable(loop)
        for binding in bindings:
            values = loop_iteration_values(loop, scope, binding)
            if values is None:
                # Bounds that are not constants leave this genvar unbound: an expression that uses it is
                # unknown, while the outer loops' values still count.
                extended.append(binding)
                continue
            extended.extend({**binding, name: value} for value in values)  # type: ignore[dict-item]
            if len(extended) > _MAX_BINDINGS:
                return None
        bindings = extended

    return [
        binding
        for binding in bindings
        if all(_branch_selected(parent, branch, scope, binding) for parent, branch in conditionals)
    ]


def evaluate_under(expr: object, scope: object, binding: Binding) -> int | None:
    """`evaluate_constant_expression` with the genvars in `binding` bound to their values."""
    return _evaluate(expr, scope, binding)
