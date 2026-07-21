from ...parser.syntax import (
    assignment_target_identifier_name,
    conditional_statement_body,
    conditional_statement_has_else,
    expression_statement_expression,
    is_always_comb_block,
    is_block_statement,
    is_conditional_statement,
    iter_assignment_nodes,
    iter_statement_nodes,
    procedural_block_statement,
)
from ...parser.types import SyntaxNode
from ..base_rule import Rule
from .rule_runner import rule_runner


def _unconditional_assignment_targets(statement: SyntaxNode) -> set[str]:
    if is_block_statement(statement):
        names: set[str] = set()
        for child in iter_statement_nodes(statement):
            if is_conditional_statement(child):
                continue
            names.update(_unconditional_assignment_targets(child))
        return names

    expr = expression_statement_expression(statement)
    if expr is None:
        return set()

    name = assignment_target_identifier_name(expr)
    return {name} if name is not None else set()


def _conditional_assignment_targets(statement: SyntaxNode) -> set[str]:
    names: set[str] = set()
    for assignment in iter_assignment_nodes(statement):
        name = assignment_target_identifier_name(assignment)
        if name is not None:
            names.add(name)
    return names


def _has_latch_pattern(statement: SyntaxNode) -> bool:
    assigned_before: set[str] = set()

    for child in iter_statement_nodes(statement):
        if is_conditional_statement(child):
            if conditional_statement_has_else(child):
                continue

            branch = conditional_statement_body(child)
            if branch is None:
                continue

            conditional_targets = _conditional_assignment_targets(branch)
            if any(name not in assigned_before for name in conditional_targets):
                return True
            continue

        assigned_before.update(_unconditional_assignment_targets(child))

    return False


@rule_runner.register
class NoLatchInAlwaysCombRule(Rule):
    code = "NO_LATCH_IN_ALWAYS_COMB"
    message = "always_comb block contains a conditional-only assignment that can infer latch-like storage"

    def applies(self, vnode, ctx) -> bool:
        if not is_always_comb_block(vnode.raw):
            return False

        statement = procedural_block_statement(vnode.raw)
        if statement is None:
            return False

        return _has_latch_pattern(statement)
