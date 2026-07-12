import pyslang as sl

from .types import DefaultCaseItemNode, ProceduralBlockNode, SyntaxNode


ALWAYS_BLOCK_KIND = sl.SyntaxKind.AlwaysBlock
ALWAYS_COMB_BLOCK_KIND = sl.SyntaxKind.AlwaysCombBlock
ALWAYS_LATCH_BLOCK_KIND = sl.SyntaxKind.AlwaysLatchBlock
INITIAL_BLOCK_KIND = sl.SyntaxKind.InitialBlock
FINAL_BLOCK_KIND = sl.SyntaxKind.FinalBlock
ENDCASE_TOKEN_KIND = sl.TokenKind.EndCaseKeyword

ASSIGNMENT_KINDS = {
    sl.SyntaxKind.AssignmentExpression,
    sl.SyntaxKind.NonblockingAssignmentExpression,
}

PROCEDURAL_BLOCK_KINDS = {
    ALWAYS_BLOCK_KIND,
    ALWAYS_COMB_BLOCK_KIND,
    ALWAYS_LATCH_BLOCK_KIND,
    INITIAL_BLOCK_KIND,
    FINAL_BLOCK_KIND,
}

CASE_STYLE_TOKEN_KINDS = {
    sl.TokenKind.CaseXKeyword,
    sl.TokenKind.CaseZKeyword,
}


def is_assignment_expression(raw: object) -> bool:
    return getattr(raw, "kind", None) in ASSIGNMENT_KINDS


def is_procedural_block(raw: object) -> bool:
    return isinstance(raw, ProceduralBlockNode) or getattr(raw, "kind", None) in PROCEDURAL_BLOCK_KINDS


def is_blocking_assignment_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == sl.TokenKind.Equals


def is_nonblocking_assignment_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == sl.TokenKind.LessThanEquals


def is_casex_casez_token(raw: object) -> bool:
    return getattr(raw, "kind", None) in CASE_STYLE_TOKEN_KINDS


def is_endcase_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == ENDCASE_TOKEN_KIND


def is_case_generate_keyword_pair(raw: object) -> bool:
    return str(getattr(raw, "keyword", "")).strip() == "case" and str(getattr(raw, "endCase", "")).strip() == "endcase"


def has_default_case_item(raw: object) -> bool:
    items = getattr(raw, "items", [])
    return any(isinstance(item, DefaultCaseItemNode) for item in items)


def is_posedge_event(raw: object) -> bool:
    return str(getattr(raw, "edge", "")) == "posedge"


def is_negedge_event(raw: object) -> bool:
    return str(getattr(raw, "edge", "")) == "negedge"


def module_declaration_name(raw: object) -> str | None:
    header = getattr(raw, "header", None)
    name = getattr(header, "name", None)
    value = getattr(name, "value", None)
    return value if isinstance(value, str) and value else None


def declarator_name(raw: object) -> str | None:
    name = getattr(raw, "name", None)
    value = getattr(name, "value", None)
    return value if isinstance(value, str) and value else None


def instantiation_type_name(raw: object) -> str | None:
    type_node = getattr(raw, "type", None)
    value = getattr(type_node, "value", None)
    return value if isinstance(value, str) and value else None


def hierarchical_instance_name(raw: object) -> str | None:
    decl = getattr(raw, "decl", None)
    name = getattr(decl, "name", None)
    value = getattr(name, "value", None)
    return value if isinstance(value, str) and value else None


def contains_descendant(root: SyntaxNode, target: SyntaxNode) -> bool:
    if root is target:
        return True
    for child in root:
        if isinstance(child, SyntaxNode) and contains_descendant(child, target):
            return True
    return False


def assignment_left(raw: object) -> SyntaxNode | None:
    if not is_assignment_expression(raw):
        return None
    left = getattr(raw, "left", None)
    return left if isinstance(left, SyntaxNode) else None


def identifier_is_assignment_lhs(ctx, raw_identifier: SyntaxNode) -> bool:
    for ancestor in reversed(ctx.stack):
        left = assignment_left(ancestor.raw)
        if left is not None:
            return contains_descendant(left, raw_identifier)
    return False


def iter_assignment_nodes(node: SyntaxNode):
    if is_assignment_expression(node):
        yield node

    for child in node:
        if not isinstance(child, SyntaxNode):
            continue
        if isinstance(child, ProceduralBlockNode):
            continue
        yield from iter_assignment_nodes(child)
