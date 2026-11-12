from ..types import RawNode, SyntaxNode, SyntaxTree, Token


def source_text_for_node(raw: object, tree: SyntaxTree | None) -> str | None:
    source_range = getattr(raw, "sourceRange", None)
    start = getattr(source_range, "start", None)
    end = getattr(source_range, "end", None)
    if start is None or end is None or tree is None:
        if raw is not None:
            text = str(raw).strip()
            return " ".join(text.split()) or None
        return None

    try:
        source = tree.sourceManager.getSourceText(start.buffer)
        snippet = source[start.offset:end.offset]
        normalized = " ".join(snippet.split())
        return normalized or None
    except (UnicodeDecodeError, Exception):
        if raw is not None:
            text = str(raw).strip()
            return " ".join(text.split()) or None
        return None


def syntax_node_snippet(raw: object) -> str:
    return str(raw)


def raw_node_children(raw: object) -> list[RawNode]:
    if isinstance(raw, Token):
        return []
    try:
        return [child for child in raw if isinstance(child, (SyntaxNode, Token))]
    except TypeError:
        return []


def same_expression(first: object, second: object, max_nodes: int = 4096) -> bool:
    """True when two syntax nodes have the same shape and the same token at every leaf, so `r[i]` is the
    same reference as `r[i]` and a different one from `r[i-1]`, `r[j]` or `r`. Whitespace and comments
    do not count. Two nodes that are too large to compare in `max_nodes` steps are reported as different."""
    pending: list[tuple[object, object]] = [(first, second)]
    for _ in range(max_nodes):
        if not pending:
            return True
        a, b = pending.pop()
        a_is_token, b_is_token = isinstance(a, Token), isinstance(b, Token)
        if a_is_token or b_is_token:
            if not (a_is_token and b_is_token):
                return False
            if a.kind != b.kind or a.valueText != b.valueText:
                return False
            continue
        if getattr(a, "kind", None) != getattr(b, "kind", None):
            return False
        a_children, b_children = raw_node_children(a), raw_node_children(b)
        if len(a_children) != len(b_children):
            return False
        pending.extend(zip(a_children, b_children))
    return False


def simple_identifier_text(expr_text: str | None) -> str | None:
    if expr_text is None:
        return None
    s = expr_text.strip()
    if s and (s[0].isalpha() or s[0] == "_") and all(c.isalnum() or c in ("_", "$") for c in s[1:]):
        return s
    return None



def node_location(raw: object, tree: SyntaxTree | None) -> dict[str, int | str] | None:
    source_range = getattr(raw, "sourceRange", None)
    start = getattr(source_range, "start", None)
    if start is None or tree is None:
        return None
    sm = getattr(tree, "sourceManager", None)
    if sm is None:
        return None
    try:
        return {
            "line": sm.getLineNumber(start),
            "col": sm.getColumnNumber(start),
            "file": str(sm.getFileName(start)),
        }
    except Exception:
        return None


def token_location(raw: object, tree: SyntaxTree | None) -> dict[str, int | str] | None:
    loc = getattr(raw, "location", None)
    if not loc or tree is None:
        return None
    sm = getattr(tree, "sourceManager", None)
    if sm is None:
        return None
    try:
        return {
            "line": sm.getLineNumber(loc),
            "col": sm.getColumnNumber(loc),
            "file": str(sm.getFileName(loc)),
        }
    except Exception:
        return None


def token_raw_text(raw: object) -> str:
    text = getattr(raw, "rawText", None)
    return text if isinstance(text, str) else ""


def identifier_name(raw: object) -> str | None:
    identifier = getattr(raw, "identifier", None)
    if identifier is not None:
        value = getattr(identifier, "value", None)
        if isinstance(value, str) and value:
            return value
    value = getattr(raw, "value", None)
    if isinstance(value, str) and value:
        return value
    raw_text = getattr(raw, "rawText", None)
    if isinstance(raw_text, str) and raw_text.strip():
        return raw_text.strip()
    return None
