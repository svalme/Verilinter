import re

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
    return [child for child in raw if isinstance(child, (SyntaxNode, Token))]


def simple_identifier_text(expr_text: str | None) -> str | None:
    if expr_text is None:
        return None
    match = re.fullmatch(r"\s*([a-zA-Z_][a-zA-Z0-9_$]*)\s*", expr_text)
    return match.group(1) if match is not None else None


def _split_top_level(text: str, separator: str) -> list[str]:
    parts: list[str] = []
    depth_brace = 0
    depth_bracket = 0
    depth_paren = 0
    start = 0
    for index, char in enumerate(text):
        if char == "{":
            depth_brace += 1
        elif char == "}":
            depth_brace -= 1
        elif char == "[":
            depth_bracket += 1
        elif char == "]":
            depth_bracket -= 1
        elif char == "(":
            depth_paren += 1
        elif char == ")":
            depth_paren -= 1
        elif (
            char == separator
            and depth_brace == 0
            and depth_bracket == 0
            and depth_paren == 0
        ):
            parts.append(text[start:index].strip())
            start = index + 1
    parts.append(text[start:].strip())
    return [part for part in parts if part]


def simple_packed_width(type_text: str | None) -> int | None:
    if not type_text:
        return None
    match = re.search(r"\[\s*(-?\d+)\s*:\s*(-?\d+)\s*\]", type_text)
    if match is None:
        if "[" in type_text and "]" in type_text:
            return None
        return 1 if type_text.strip() else None
    left = int(match.group(1))
    right = int(match.group(2))
    return abs(left - right) + 1


def simple_packed_range(type_text: str | None) -> tuple[int | None, int | None]:
    if not type_text:
        return None, None
    match = re.search(r"\[\s*(-?\d+)\s*:\s*(-?\d+)\s*\]", type_text)
    if match is None:
        if "[" in type_text and "]" in type_text:
            return None, None
        return (0, 0) if type_text.strip() else (None, None)
    return int(match.group(1)), int(match.group(2))


def type_text_width_and_signed(type_text: str | None) -> tuple[int | None, bool | None]:
    if type_text is None:
        return None, None
    return simple_packed_width(type_text), bool(re.search(r"\bsigned\b", type_text))


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
    value = getattr(identifier, "value", None)
    return value if isinstance(value, str) and value else None
