"""Generate-block shape queries: labeled/unlabeled `begin...end` bodies of
if/loop/case-generate branches, and label redefinition between generate constructs."""

from ...syntax_kinds import GENERATE_BLOCK_KIND, GENVAR_KEYWORD_KIND


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


def generate_block_label(raw: object) -> str | None:
    """The `: label` of a generate block's `begin`, or None when it has none."""
    if not is_generate_block_node(raw):
        return None
    begin_name = getattr(raw, "beginName", None)
    value = getattr(getattr(begin_name, "name", None), "value", None)
    return value if isinstance(value, str) and value else None


_MAX_GENERATE_ANCESTORS = 64


def generate_construct_labels(raw: object) -> set[str]:
    """The explicit labels the generate blocks of one construct can put in their scope: an if-generate
    with its whole else and else-if chain, a case-generate, a loop-generate, or a bare generate block.

    Only one branch of an if or case is elaborated, so the branches of one construct never coexist and may
    share a label; the construct's labels are the names it can add to the scope that holds it."""
    from ..node_kind_checks import is_case_generate_node, is_if_generate_node, is_loop_generate_node

    found: list[str | None] = []
    if is_if_generate_node(raw):
        node: object = raw
        for _ in range(_MAX_GENERATE_ANCESTORS):
            found.append(generate_block_label(getattr(node, "block", None)))
            clause = getattr(getattr(node, "elseClause", None), "clause", None)
            if not is_if_generate_node(clause):
                found.append(generate_block_label(clause))
                break
            node = clause
    elif is_case_generate_node(raw):
        found.extend(generate_block_label(getattr(item, "clause", None)) for item in getattr(raw, "items", None) or ())
    elif is_loop_generate_node(raw):
        found.append(generate_block_label(getattr(raw, "block", None)))
    else:
        found.append(generate_block_label(raw))
    return {label for label in found if label is not None}


def _scope_constructs(raw: object) -> list[object] | None:
    """The generate constructs written directly in the scope that holds `raw`, in source order, or None when
    `raw` is not itself one of them (a branch block, or the `else if` of a chain). A `generate ... endgenerate`
    region adds its members to the scope that holds it."""
    from ...syntax_kinds import GENERATE_REGION_KIND

    parent = getattr(raw, "parent", None)
    if getattr(parent, "members", None) is None:
        return None
    scope = parent
    for _ in range(_MAX_GENERATE_ANCESTORS):
        if getattr(scope, "kind", None) != GENERATE_REGION_KIND:
            break
        scope = getattr(scope, "parent", None)
    members: list[object] = []
    for member in getattr(scope, "members", None) or ():
        if getattr(member, "kind", None) == GENERATE_REGION_KIND:
            members.extend(getattr(member, "members", None) or ())
        else:
            members.append(member)
    return members


def generate_label_redefined(raw: object) -> bool:
    """True if `raw` is a generate construct (an `if`, `case` or loop generate, or a bare generate block) that
    gives a block an explicit label an earlier generate construct in the same scope already uses.

    Two constructs in one scope are both elaborated, so their blocks coexist and a shared label is a
    redefinition, even when their conditions exclude each other. The branches of one construct are not
    compared with each other (see `generate_construct_labels`), and neither are labels in different scopes
    (another module, or a block nested inside a generate block). An unlabeled block has no label to share.
    """
    labels = generate_construct_labels(raw)
    if not labels:
        return False
    for member in _scope_constructs(raw) or ():
        if member is raw:
            return False
        if labels & generate_construct_labels(member):
            return True
    return False


def taken_case_item(case_raw: object, scope: object) -> object | None:
    """The item of a case-generate that the default parameter values select, or None when that cannot
    be decided (a condition or label that is not constant, or a label list that is not understood)."""
    from ..expressions.constant_evaluation import evaluate_constant_expression
    from ...syntax_kinds import DEFAULT_CASE_ITEM_KIND, STANDARD_CASE_ITEM_KIND

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
    from ..expressions.constant_evaluation import evaluate_constant_expression
    from ..node_kind_checks import is_case_generate_node, is_if_generate_node

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
