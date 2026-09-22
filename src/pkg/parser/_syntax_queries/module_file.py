from pathlib import Path, PurePath
import re

from ..syntax_kinds import COMPILATION_UNIT_KIND, MODULE_DECLARATION_KIND
from ..types import SyntaxTree


def module_declaration_name(raw: object) -> str | None:
    header = getattr(raw, "header", None)
    name = getattr(header, "name", None)
    value = getattr(name, "value", None)
    return value if isinstance(value, str) and value else None


def module_declaration_names_in_file(tree: SyntaxTree) -> list[str]:
    from ..syntax_queries import is_module_declaration_node

    root = tree.root
    names: list[str] = []
    if getattr(root, "kind", None) == COMPILATION_UNIT_KIND:
        for member in getattr(root, "members", None) or []:
            if getattr(member, "kind", None) != MODULE_DECLARATION_KIND:
                continue
            name = module_declaration_name(member)
            if name:
                names.append(name)
        return names
    if is_module_declaration_node(root):
        name = module_declaration_name(root)
        if name:
            names.append(name)
    return names


def module_declaration_file_stem(current_file: str | None) -> str | None:
    if not current_file:
        return None
    return PurePath(current_file).stem


def is_module_filename_mismatch(raw: object, tree: SyntaxTree, current_file: str | None) -> bool:
    from ..syntax_queries import is_first_module_declaration_in_file

    if not is_first_module_declaration_in_file(raw, tree):
        return False
    stem = module_declaration_file_stem(current_file)
    if not stem:
        return False
    return stem not in module_declaration_names_in_file(tree)


def primitive_declaration_name(raw: object) -> str | None:
    name = getattr(raw, "name", None)
    value = getattr(name, "value", None)
    return value if isinstance(value, str) and value else None


def is_module_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == MODULE_DECLARATION_KIND


def is_first_module_declaration_in_file(raw: object, tree: SyntaxTree) -> bool:
    if not is_module_declaration_node(raw):
        return False
    root = tree.root
    if getattr(root, "kind", None) == COMPILATION_UNIT_KIND:
        members = getattr(root, "members", None)
        if members is None:
            return False
        for member in members:
            if getattr(member, "kind", None) == MODULE_DECLARATION_KIND:
                return member is raw
        return False
    return root is raw


def is_extra_module_declaration_in_file(raw: object, tree: SyntaxTree) -> bool:
    if not is_module_declaration_node(raw):
        return False
    root = tree.root
    if getattr(root, "kind", None) != COMPILATION_UNIT_KIND:
        return False
    members = getattr(root, "members", None)
    if members is None:
        return False
    seen_first = False
    for member in members:
        if getattr(member, "kind", None) != MODULE_DECLARATION_KIND:
            continue
        if not seen_first:
            seen_first = True
            continue
        if member is raw:
            return True
    return False


TIMESCALE_DIRECTIVE_RE = re.compile(r"`timescale\b")


def has_timescale_directive_before(raw: object, tree: SyntaxTree) -> bool:
    source_range = getattr(raw, "sourceRange", None)
    start = getattr(source_range, "start", None)
    if start is None:
        return False
    try:
        source = tree.sourceManager.getSourceText(start.buffer)
    except (UnicodeDecodeError, Exception):
        source_manager = getattr(tree, "sourceManager", None)
        full_path = source_manager.getFullPath(start.buffer) if source_manager else None
        if full_path and Path(full_path).is_file():
            source = Path(full_path).read_text(encoding="utf-8", errors="replace")
        else:
            return False
    return TIMESCALE_DIRECTIVE_RE.search(source[: start.offset]) is not None


def is_missing_timescale_directive(raw: object, tree: SyntaxTree) -> bool:
    return is_first_module_declaration_in_file(raw, tree) and not has_timescale_directive_before(raw, tree)
