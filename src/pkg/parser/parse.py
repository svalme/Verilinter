import re
from pathlib import Path

import pyslang as sl

from .types import SyntaxTree

DEFAULT_NETTYPE_NONE_RE = re.compile(r"^\s*`default_nettype\s+none\b", re.MULTILINE)


def parse_file(path: str, include_dirs: list[str] | None = None) -> SyntaxTree:
    """Parse `path`, optionally searching `include_dirs` to resolve
    `` `include "..." `` directives that reference a header outside the
    source file's own directory (pyslang's default `SourceManager` only
    looks there). Common in multi-directory repos that vendor a
    shared macro/assertion header --
    without this, every subsequent use of a macro that header defines fails
    to parse as `unknown macro or compiler directive`, corrupting the AST for
    the rest of the file. Each call owns a fresh source manager so repeated
    analyses in the same process observe file changes.
    """
    # The default pyslang source manager can retain file buffers across calls.
    # A fresh manager is required when files change within the same process.
    source_manager = sl.SourceManager()
    for directory in include_dirs or []:
        source_manager.addUserDirectories(directory)
    return SyntaxTree.fromFile(path, source_manager)


def parse_text(text: str) -> SyntaxTree:
    return SyntaxTree.fromText(text)


def text_uses_default_nettype_none(text: str) -> bool:
    return bool(DEFAULT_NETTYPE_NONE_RE.search(text))


def file_uses_default_nettype_none(path: str) -> bool:
    return text_uses_default_nettype_none(Path(path).read_text(encoding="utf-8"))
