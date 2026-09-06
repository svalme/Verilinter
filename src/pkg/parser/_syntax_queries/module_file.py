from pathlib import PurePath

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
