"""Conditional/case-statement and block-statement shape predicates: `if`/`else`
structure, begin/end wrapping, constant-condition detection, and the
`full_case`/`parallel_case` pragma comment check."""

from collections.abc import Iterator
from pathlib import Path

from ..syntax_kinds import (
    BLOCK_STATEMENT_KINDS,
    CASE_TOKEN_KINDS,
    CONDITIONAL_STATEMENT_KIND,
    ELSE_CLAUSE_KIND,
    EMPTY_STATEMENT_KIND,
    PARALLEL_BLOCK_STATEMENT_KIND,
    UNBASED_UNSIZED_LITERAL_EXPRESSION_KIND,
)
from ..types import SyntaxNode, SyntaxTree


def procedural_block_statement(raw: object) -> SyntaxNode | None:
    statement = getattr(raw, "statement", None)
    return statement if isinstance(statement, SyntaxNode) else None


def is_conditional_statement(raw: object) -> bool:
    return getattr(raw, "kind", None) == CONDITIONAL_STATEMENT_KIND


def conditional_statement_has_else(raw: object) -> bool:
    return getattr(raw, "elseClause", None) is not None


def conditional_statement_body(raw: object) -> SyntaxNode | None:
    statement = getattr(raw, "statement", None)
    return statement if isinstance(statement, SyntaxNode) else None


def is_block_statement(raw: object) -> bool:
    return getattr(raw, "kind", None) in BLOCK_STATEMENT_KINDS


def is_else_clause_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == ELSE_CLAUSE_KIND


def else_clause_body(raw: object) -> SyntaxNode | None:
    clause = getattr(raw, "clause", None)
    return clause if isinstance(clause, SyntaxNode) else None


def conditional_statement_else_body(raw: object) -> SyntaxNode | None:
    else_clause = getattr(raw, "elseClause", None)
    if else_clause is None:
        return None
    return else_clause_body(else_clause)


def is_conditional_constant_expression(raw: object) -> bool:
    """True if `raw` is a runtime procedural `if` statement whose condition
    predicate statically evaluates to a constant boolean value (e.g. 0, 1, 1'b0,
    1'b1, '0, '1, or a pure constant expression like 1 == 0).
    Excludes `generate if` statements (`IfGenerateSyntax`)."""
    if not is_conditional_statement(raw):
        return False

    predicate = getattr(raw, "predicate", None)
    conditions = getattr(predicate, "conditions", None) or []
    if not conditions:
        return False

    from .procedural import _iter_identifier_nodes
    from .expressions import evaluate_constant_expression, unwrap_parentheses
    from .literals import constant_integer_value

    for condition in conditions:
        expr = getattr(condition, "expr", None)
        if expr is None:
            continue
        unwrapped = unwrap_parentheses(expr)
        if getattr(unwrapped, "kind", None) == UNBASED_UNSIZED_LITERAL_EXPRESSION_KIND:
            return True
        val = constant_integer_value(unwrapped)
        if val is not None:
            return True
        idents = list(_iter_identifier_nodes(unwrapped))
        if not idents:
            eval_val = evaluate_constant_expression(unwrapped)
            if eval_val is not None:
                return True
    return False



def is_unwrapped_if_body(raw: object) -> bool:
    """True if a ConditionalStatementSyntax's `if` branch is a single statement
    not wrapped in begin/end."""
    if not is_conditional_statement(raw):
        return False
    body = conditional_statement_body(raw)
    return isinstance(body, SyntaxNode) and not is_block_statement(body)


def is_unwrapped_else_body(raw: object) -> bool:
    """True if an ElseClauseSyntax's body is a single statement not wrapped in
    begin/end and not itself an `else if` chain."""
    if not is_else_clause_node(raw):
        return False
    body = else_clause_body(raw)
    return (
        isinstance(body, SyntaxNode)
        and not is_block_statement(body)
        and not is_conditional_statement(body)
    )


def is_parallel_block_statement(raw: object) -> bool:
    return getattr(raw, "kind", None) == PARALLEL_BLOCK_STATEMENT_KIND


def iter_statement_nodes(raw: SyntaxNode) -> Iterator[SyntaxNode]:
    if not is_block_statement(raw):
        yield raw
        return

    items = getattr(raw, "items", None)
    if items is None:
        return

    for child in items:
        if isinstance(child, SyntaxNode):
            yield child


def expression_statement_expression(raw: object) -> SyntaxNode | None:
    expr = getattr(raw, "expr", None)
    return expr if isinstance(expr, SyntaxNode) else None


def has_full_parallel_case_pragma(raw: object, tree: SyntaxTree) -> bool:
    if getattr(raw, "kind", None) not in CASE_TOKEN_KINDS:
        return False
    location = getattr(raw, "location", None)
    if location is None:
        return False

    source_manager = tree.sourceManager
    try:
        source = source_manager.getSourceText(location.buffer)
    except (UnicodeDecodeError, Exception):
        full_path = source_manager.getFullPath(location.buffer) if source_manager else None
        if full_path and Path(full_path).is_file():
            source = Path(full_path).read_text(encoding="utf-8", errors="replace")
        else:
            return False
    line_number = source_manager.getLineNumber(location)
    lines = source.splitlines()
    if line_number <= 1 or line_number - 2 >= len(lines):
        return False

    preceding_line = lines[line_number - 2].lower()
    return "full_case" in preceding_line or "parallel_case" in preceding_line


def is_empty_conditional_or_case_branch(raw: object) -> bool:
    """True if `raw` is an empty `begin...end` block or a bare `;`
    (`EmptyStatementSyntax`) sitting directly in an if/else/case-item branch
    position -- `ConditionalStatementSyntax.statement`, `ElseClauseSyntax.clause`,
    or a case item's `.clause`. Needs no ancestor walk, same one-level-up
    `.parent` check style as `is_unsized_literal_in_flagged_value_context`.
    """
    kind = getattr(raw, "kind", None)
    if kind == EMPTY_STATEMENT_KIND:
        is_empty = True
    elif is_block_statement(raw):
        items = getattr(raw, "items", None)
        is_empty = next(iter(items), None) is None if items is not None else True
    else:
        return False
    if not is_empty:
        return False

    parent = getattr(raw, "parent", None)
    parent_type = type(parent).__name__
    if parent_type == "ConditionalStatementSyntax":
        return getattr(parent, "statement", None) is raw
    if parent_type == "ElseClauseSyntax":
        return getattr(parent, "clause", None) is raw
    if parent_type in ("StandardCaseItemSyntax", "DefaultCaseItemSyntax"):
        return getattr(parent, "clause", None) is raw
    return False
