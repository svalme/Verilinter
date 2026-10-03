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
