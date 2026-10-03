"""Loop statement classification, termination analysis, and infinite-loop queries."""
from __future__ import annotations

from ..syntax_kinds import (
    BREAK_KEYWORD_TOKEN_KIND,
    DELAY_CONTROL_KINDS,
    DISABLE_STATEMENT_KIND,
    DO_WHILE_STATEMENT_KIND,
    EVENT_CONTROL_KINDS,
    EVENT_TRIGGER_STATEMENT_KIND,
    EXPRESSION_STATEMENT_KIND,
    FOREVER_STATEMENT_KIND,
    FOR_LOOP_STATEMENT_KIND,
    INVOCATION_EXPRESSION_KIND,
    JUMP_STATEMENT_KIND,
    LOOP_STATEMENT_KIND,
    RETURN_STATEMENT_KIND,
    TIMING_CONTROL_STATEMENT_KIND,
    UNBASED_UNSIZED_LITERAL_EXPRESSION_KIND,
    WAIT_STATEMENT_KIND,
    WHILE_TOKEN_KIND,
)
from ..traversal_guard import guarded_traversal
from ..types import SyntaxNode
from .expressions import evaluate_constant_expression, unwrap_parentheses
from .literals import constant_integer_value
from .system_tasks import system_task_name

LOOP_STATEMENT_KINDS = {
    FOREVER_STATEMENT_KIND,
    LOOP_STATEMENT_KIND,
    DO_WHILE_STATEMENT_KIND,
    FOR_LOOP_STATEMENT_KIND,
}

_EXIT_OR_TIMING_KINDS = {
    RETURN_STATEMENT_KIND,
    DISABLE_STATEMENT_KIND,
    TIMING_CONTROL_STATEMENT_KIND,
    WAIT_STATEMENT_KIND,
    EVENT_TRIGGER_STATEMENT_KIND,
} | DELAY_CONTROL_KINDS | EVENT_CONTROL_KINDS


def is_loop_statement(raw: object) -> bool:
    """True if `raw` is a procedural loop statement (`forever`, `while`,
    `do-while`, or `for`)."""
    return getattr(raw, "kind", None) in LOOP_STATEMENT_KINDS


def loop_statement_body(raw: object) -> SyntaxNode | None:
    """Return the inner statement body of a loop node, or `None`."""
    if not is_loop_statement(raw):
        return None
    stmt = getattr(raw, "statement", None)
    return stmt if isinstance(stmt, SyntaxNode) else None


def is_loop_condition_constantly_true(raw: object, scope: object = None) -> bool:
    """True if `raw` is a procedural loop whose loop condition is statically
    known to be constantly true (e.g. `forever`, `while (1)`, `for (;;)`)."""
    kind = getattr(raw, "kind", None)
    if kind == FOREVER_STATEMENT_KIND:
        return True

    if kind == LOOP_STATEMENT_KIND:
        repeat_or_while = getattr(raw, "repeatOrWhile", None)
        if getattr(repeat_or_while, "kind", None) != WHILE_TOKEN_KIND:
            return False
        expr = getattr(raw, "expr", None)
        return _is_expression_constantly_true(expr, scope=scope)

    if kind == DO_WHILE_STATEMENT_KIND:
        expr = getattr(raw, "expr", None)
        return _is_expression_constantly_true(expr, scope=scope)

    if kind == FOR_LOOP_STATEMENT_KIND:
        stop_expr = getattr(raw, "stopExpr", None)
        if stop_expr is None:
            # IEEE 1800-2017 §12.7.1: omitted stopExpr defaults to 1'b1
            return True
        return _is_expression_constantly_true(stop_expr, scope=scope)

    return False


def _is_expression_constantly_true(expr: object, scope: object = None) -> bool:
    if expr is None:
        return False
    unwrapped = unwrap_parentheses(expr)
    if getattr(unwrapped, "kind", None) == UNBASED_UNSIZED_LITERAL_EXPRESSION_KIND:
        tok = getattr(unwrapped, "literal", None)
        if tok is not None:
            text = str(tok).strip().lstrip("'").lower()
            return text == "1"
    val = constant_integer_value(unwrapped)
    if val is not None:
        return val != 0
    eval_val = evaluate_constant_expression(unwrapped, scope=scope)
    if eval_val is not None:
        return eval_val != 0
    return False


@guarded_traversal(max_depth=64, default=False)
def has_loop_exit_or_timing_control(statement_node: object, allow_break: bool = True) -> bool:
    """True if `statement_node` contains an escape statement (`break`, `return`,
    `disable`, `$finish`, `$fatal`, `$stop`, `$exit`) or a timing/event control
    (`#`, `@`, `wait`) that prevents an infinite loop from hanging simulation.
    Breaks inside nested child loops do not escape the outer loop."""
    if statement_node is None:
        return False

    from ..syntax import raw_node_children

    kind = getattr(statement_node, "kind", None)

    if kind in _EXIT_OR_TIMING_KINDS:
        return True

    if kind == JUMP_STATEMENT_KIND and allow_break:
        tok = getattr(statement_node, "breakOrContinue", None)
        if getattr(tok, "kind", None) == BREAK_KEYWORD_TOKEN_KIND:
            return True

    if kind == EXPRESSION_STATEMENT_KIND:
        expr = getattr(statement_node, "expr", None)
        expr_kind = getattr(expr, "kind", None)
        callee = getattr(expr, "left", None) if expr_kind == INVOCATION_EXPRESSION_KIND else expr
        sys_name = system_task_name(callee)
        if sys_name in {"$finish", "$fatal", "$stop", "$exit"}:
            return True

    is_nested_loop = kind in LOOP_STATEMENT_KINDS
    child_allow_break = False if is_nested_loop else allow_break

    for child in raw_node_children(statement_node):
        if has_loop_exit_or_timing_control(child, allow_break=child_allow_break):
            return True

    return False


def is_infinite_loop(raw: object, scope: object = None) -> bool:
    """True if `raw` is a procedural loop whose condition is constantly true
    and whose body contains no loop exit (`break`, `return`, `disable`, `$finish`)
    or timing/event control (`#`, `@`, `wait`)."""
    if not is_loop_condition_constantly_true(raw, scope=scope):
        return False
    body = loop_statement_body(raw)
    return not has_loop_exit_or_timing_control(body, allow_break=True)
