from typing import TYPE_CHECKING

from ...parser.syntax import (
    assignment_target_identifier_name,
    case_item_clause,
    case_statement_items,
    conditional_statement_body,
    conditional_statement_else_body,
    conditional_statement_has_else,
    expression_statement_expression,
    has_default_case_item,
    is_always_comb_block,
    is_block_statement,
    is_case_statement,
    is_conditional_statement,
    iter_assignment_nodes,
    iter_statement_nodes,
    procedural_block_statement,
)
from ...parser.traversal_guard import guarded_traversal
from ...parser.types import SyntaxNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@guarded_traversal(max_depth=64, default=set())
def _unconditional_assignment_targets(statement: SyntaxNode) -> set[str]:
    if is_block_statement(statement):
        names: set[str] = set()
        for child in iter_statement_nodes(statement):
            if is_conditional_statement(child) or is_case_statement(child):
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


@guarded_traversal(max_depth=64, default=(False, set()))
def _analyze_statement_latch(statement: SyntaxNode, assigned_before: set[str]) -> tuple[bool, set[str]]:
    """Analyzes a statement or block for latch inference in combinational logic.

    Returns (has_latch, always_assigned_by_statement).
    """
    if is_block_statement(statement):
        current_assigned = set(assigned_before)
        block_always: set[str] = set()
        for child in iter_statement_nodes(statement):
            has_latch, child_always = _analyze_statement_latch(child, current_assigned)
            if has_latch:
                return True, set()
            current_assigned.update(child_always)
            block_always.update(child_always)
        return False, block_always

    if is_conditional_statement(statement):
        body = conditional_statement_body(statement)
        has_else = conditional_statement_has_else(statement)
        if not has_else:
            if body is None:
                return False, set()
            targets = _conditional_assignment_targets(body)
            if any(name not in assigned_before for name in targets):
                return True, set()
            has_latch, _ = _analyze_statement_latch(body, assigned_before)
            return has_latch, set()

        else_body = conditional_statement_else_body(statement)
        if body is None or else_body is None:
            return False, set()

        has_latch_then, always_then = _analyze_statement_latch(body, assigned_before)
        if has_latch_then:
            return True, set()
        has_latch_else, always_else = _analyze_statement_latch(else_body, assigned_before)
        if has_latch_else:
            return True, set()

        targets_then = _conditional_assignment_targets(body)
        targets_else = _conditional_assignment_targets(else_body)

        # A target assigned in one branch but omitted in the other, and not assigned before, infers a latch
        asymmetric = (targets_then ^ targets_else) - assigned_before
        if asymmetric:
            return True, set()

        return False, (always_then & always_else)

    if is_case_statement(statement):
        items = case_statement_items(statement)
        has_default = has_default_case_item(statement)
        if not has_default:
            for it in items:
                clause = case_item_clause(it)
                if clause is not None:
                    targets = _conditional_assignment_targets(clause)
                    if any(name not in assigned_before for name in targets):
                        return True, set()
                    has_latch, _ = _analyze_statement_latch(clause, assigned_before)
                    if has_latch:
                        return True, set()
            return False, set()

        item_always = []
        item_targets_list = []
        for it in items:
            clause = case_item_clause(it)
            if clause is None:
                continue
            has_latch, always = _analyze_statement_latch(clause, assigned_before)
            if has_latch:
                return True, set()
            item_always.append(always)
            item_targets_list.append(_conditional_assignment_targets(clause))

        if item_targets_list:
            all_targets = set.union(*item_targets_list)
            common_targets = set.intersection(*item_targets_list)
            if any(name not in assigned_before for name in (all_targets - common_targets)):
                return True, set()
            always_all = set.intersection(*item_always) if item_always else set()
            return False, always_all
        return False, set()

    unconditional = _unconditional_assignment_targets(statement)
    return False, unconditional


def has_latch_pattern(statement: SyntaxNode) -> bool:
    has_latch, _ = _analyze_statement_latch(statement, set())
    return has_latch


_has_latch_pattern = has_latch_pattern



@rule_runner.register
class NoLatchInAlwaysCombRule(Rule):
    code = "NO_LATCH_IN_ALWAYS_COMB"
    message = "always_comb block contains a conditional-only assignment that can infer latch-like storage"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        if not is_always_comb_block(vnode.raw):
            return False

        statement = procedural_block_statement(vnode.raw)
        if statement is None:
            return False

        return _has_latch_pattern(statement)
