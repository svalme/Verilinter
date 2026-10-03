import hashlib
from pathlib import Path
from typing import Any

import pyslang as sl

from .syntax_kinds import DEFAULT_NETTYPE_DIRECTIVE_KIND
from .types import SyntaxNode, SyntaxTree
from ._syntax_queries.package_scoping import tree_has_package_declaration


def parse_file(
    path: str | Path,
    include_dirs: list[str] | None = None,
    defines: list[str] | None = None,
) -> SyntaxTree:
    """Parse `path`, optionally searching `include_dirs` to resolve
    `` `include "..." `` directives that reference a header outside the
    source file's own directory (pyslang's default `SourceManager` only
    looks there), and configuring preprocessor macro defines (from `-D`).
    Each call owns a fresh source manager so repeated analyses in the same
    process observe file changes.
    """
    source_manager = sl.SourceManager()
    for directory in include_dirs or []:
        source_manager.addUserDirectories(directory)

    bag = sl.Bag()
    if defines:
        pp = sl.PreprocessorOptions()
        pp.predefines = list(defines)
        bag.preprocessorOptions = pp

    return SyntaxTree.fromFile(str(path), source_manager, options=bag)


def parse_text(text: str, defines: list[str] | None = None) -> SyntaxTree:
    if defines:
        bag = sl.Bag()
        pp = sl.PreprocessorOptions()
        pp.predefines = list(defines)
        bag.preprocessorOptions = pp
        source_manager = sl.SourceManager()
        return SyntaxTree.fromText(text, source_manager, options=bag)
    return SyntaxTree.fromText(text)


def extract_header_dependencies(tree: SyntaxTree) -> list[dict[str, str]]:
    """Extract all directly and transitively included header files from a parsed
    SyntaxTree, returning their canonical file paths and SHA-256 hashes."""
    dependencies: list[dict[str, str]] = []
    seen: set[str] = set()
    source_manager = getattr(tree, "sourceManager", None)
    if source_manager is None:
        return []
    include_directives = getattr(tree, "getIncludeDirectives", None)
    if include_directives is None:
        return []
    for inc in include_directives():
        buf = getattr(inc, "buffer", None)
        buf_id = getattr(buf, "id", None)
        if buf_id is None:
            continue
        raw_path = source_manager.getFullPath(buf_id)
        if not raw_path:
            continue
        p = Path(raw_path).resolve()
        norm_key = str(p)
        if norm_key in seen:
            continue
        seen.add(norm_key)
        try:
            if p.is_file():
                h = hashlib.sha256(p.read_bytes()).hexdigest()
                dependencies.append({"path": norm_key, "hash": h})
        except OSError:
            pass
    return dependencies


def tree_uses_default_nettype_none(tree: SyntaxTree | None) -> bool:
    if tree is None:
        return False
    root = getattr(tree, "root", None)
    if root is None or not isinstance(root, SyntaxNode):
        return False
    tok = getattr(root, "getFirstToken", lambda: None)()
    end_of_file = getattr(sl.TokenKind, "EndOfFile", None)
    depth = 0
    while tok is not None and getattr(tok, "kind", None) != end_of_file and depth < 1_000_000:
        depth += 1
        for tr in getattr(tok, "trivia", ()):
            syn = getattr(tr, "syntax", None)
            if callable(syn):
                syn = syn()
            if getattr(syn, "kind", None) == DEFAULT_NETTYPE_DIRECTIVE_KIND:
                net_type = getattr(syn, "netType", None)
                if str(net_type).strip() == "none":
                    return True
        tok = getattr(tok, "getNextToken", lambda: None)()
    return False


def text_uses_default_nettype_none(text: str) -> bool:
    try:
        tree = parse_text(text)
        return tree_uses_default_nettype_none(tree)
    except Exception:
        return False


def file_uses_default_nettype_none(path: str | Path) -> bool:
    try:
        tree = parse_file(str(path))
        return tree_uses_default_nettype_none(tree)
    except Exception:
        return False


def extract_parse_diagnostics(tree: SyntaxTree, default_file: str) -> list[dict[str, Any]]:
    """Extract real syntax and parse errors from a SyntaxTree into standard
    diagnostic dictionaries with code 'PARSER_ERROR' and severity 'error'."""
    diagnostics = getattr(tree, "diagnostics", None)
    if not diagnostics:
        return []

    errors: list[dict[str, Any]] = []
    source_manager = getattr(tree, "sourceManager", None)
    engine = sl.DiagnosticEngine(source_manager) if source_manager is not None else None

    for d in diagnostics:
        is_error = getattr(d, "isError", None)
        if is_error is not None and not is_error():
            continue

        loc = getattr(d, "location", None)
        line = 0
        col = 0
        file_name = default_file
        if source_manager is not None and loc is not None:
            try:
                line = source_manager.getLineNumber(loc)
                col = source_manager.getColumnNumber(loc)
                raw_file = source_manager.getFileName(loc)
                if raw_file and raw_file != "source":
                    file_name = str(raw_file)
            except Exception:
                pass

        if engine is not None:
            try:
                msg = engine.formatMessage(d)
            except Exception:
                msg = str(d)
        else:
            msg = str(d)

        errors.append(
            {
                "code": "PARSER_ERROR",
                "message": f"syntax error: {msg}",
                "file": file_name,
                "line": line,
                "col": col,
                "severity": "error",
                "category": "syntax_and_structure",
            }
        )
    return errors
