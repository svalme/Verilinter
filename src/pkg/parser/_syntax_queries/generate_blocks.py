"""Generate-block shape queries: labeled/unlabeled `begin...end` bodies of
if/loop/case-generate branches, and duplicate branch-label detection."""

from ..syntax_kinds import GENERATE_BLOCK_KIND, GENVAR_KEYWORD_KIND


def is_generate_block_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == GENERATE_BLOCK_KIND


def loop_generate_genvar_name(raw: object) -> str | None:
    """Name of the genvar declared inline in a generate-for header
    (`for (genvar i = 0; ...)`), or None when the loop reuses an outer genvar.

    The inline genvar name is a bare token, not a `DeclaratorSyntax`.
    """
    genvar_token = getattr(raw, "genvar", None)
    if getattr(genvar_token, "kind", None) != GENVAR_KEYWORD_KIND:
        return None
    ident = getattr(raw, "identifier", None)
    val = getattr(ident, "value", None)
    return val if isinstance(val, str) and val else None


def is_unlabeled_generate_block(raw: object) -> bool:
    """True if `raw` is a `GenerateBlockSyntax` (the `begin ... end` body of an
    if/loop/case-generate branch, or a bare nested block directly inside a
    `generate` region) with no `: label` on its `begin`.

    An unlabeled generate block still gets an implicit `genblkN` name during
    elaboration, but that name is index-based and shifts if a sibling branch is
    added or removed -- an explicit label keeps hierarchical paths (and
    waveform/debug views) stable. The unwrapped single-statement generate body
    (`if (cond) wire w;`, no `begin`/`end` at all) is a different, unnamed shape
    entirely -- it never becomes a `GenerateBlockSyntax`, so it is intentionally
    not covered here.
    """
    return is_generate_block_node(raw) and getattr(raw, "beginName", None) is None


def _generate_block_label(raw: object) -> str | None:
    if not is_generate_block_node(raw):
        return None
    begin_name = getattr(raw, "beginName", None)
    value = getattr(getattr(begin_name, "name", None), "value", None)
    return value if isinstance(value, str) and value else None


def duplicate_generate_branch_label(raw: object) -> bool:
    """True if `raw` (an `IfGenerateSyntax` or `CaseGenerateSyntax`) has two or
    more direct generate-block branches sharing the same explicit label --
    the `if`/`else` branches of one if-generate, or the case items of one
    case-generate. An unlabeled branch (`MISSING_GENERATE_BLOCK_LABEL`'s own
    concern) is never compared against anything here, since two unlabeled
    branches are not a genuine name collision.

    Deliberately per-construct, matching `is_unlabeled_generate_block`'s own
    anchoring: two labels colliding across two separate top-level
    `generate...endgenerate` regions in the same module are a real
    elaboration-time hierarchical-path collision too, but that needs
    module-wide generate-label collection this first pass doesn't attempt.
    """
    from .node_kind_checks import is_case_generate_node, is_if_generate_node

    labels: list[str] = []
    if is_if_generate_node(raw):
        block_label = _generate_block_label(getattr(raw, "block", None))
        if block_label is not None:
            labels.append(block_label)
        else_clause = getattr(raw, "elseClause", None)
        else_label = _generate_block_label(getattr(else_clause, "clause", None))
        if else_label is not None:
            labels.append(else_label)
    elif is_case_generate_node(raw):
        for item in getattr(raw, "items", None) or []:
            label = _generate_block_label(getattr(item, "clause", None))
            if label is not None:
                labels.append(label)
    else:
        return False

    return len(labels) != len(set(labels))


_MAX_GENERATE_ANCESTORS = 64


def taken_case_item(case_raw: object, scope: object) -> object | None:
    """The item of a case-generate that the default parameter values select, or None when that cannot
    be decided (a condition or label that is not constant, or a label list that is not understood)."""
    from .expressions import evaluate_constant_expression
    from ..syntax_kinds import DEFAULT_CASE_ITEM_KIND, STANDARD_CASE_ITEM_KIND

    selector = evaluate_constant_expression(getattr(case_raw, "condition", None), scope=scope)
    if selector is None:
        return None
    default_item = None
    for item in getattr(case_raw, "items", None) or ():
        kind = getattr(item, "kind", None)
        if kind == DEFAULT_CASE_ITEM_KIND:
            default_item = item
        elif kind == STANDARD_CASE_ITEM_KIND:
            for label in getattr(item, "expressions", None) or ():
                value = evaluate_constant_expression(label, scope=scope)
                if value is None:
                    return None
                if value == selector:
                    return item
        else:
            return None
    return default_item


def in_inactive_generate_branch(raw: object, scope: object) -> bool:
    """True when `raw` sits in an `if` or `case` generate branch that the default parameter values switch
    off. Widths, indices and drivers inside such a branch are computed from values the branch is not
    elaborated with, so a finding there describes code that does not exist for the default configuration.
    A condition that cannot be evaluated leaves the branch active."""
    from .expressions import evaluate_constant_expression
    from .node_kind_checks import is_case_generate_node, is_if_generate_node

    child = raw
    for _ in range(_MAX_GENERATE_ANCESTORS):
        parent = getattr(child, "parent", None)
        if parent is None:
            return False
        if is_if_generate_node(parent):
            condition = evaluate_constant_expression(getattr(parent, "condition", None), scope=scope)
            if condition is not None:
                else_clause = getattr(parent, "elseClause", None)
                in_then = child is getattr(parent, "block", None)
                in_else = else_clause is not None and child is else_clause
                if (in_then and condition == 0) or (in_else and condition != 0):
                    return True
        elif is_case_generate_node(parent) and any(child is item for item in getattr(parent, "items", None) or ()):
            taken = taken_case_item(parent, scope)
            if taken is not None and taken is not child:
                return True
        child = parent
    return False
