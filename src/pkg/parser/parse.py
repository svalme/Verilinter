import re
from pathlib import Path

from .types import SyntaxTree

DEFAULT_NETTYPE_NONE_RE = re.compile(r"^\s*`default_nettype\s+none\b", re.MULTILINE)


def parse_file(path: str) -> SyntaxTree:
    return SyntaxTree.fromFile(path)


def parse_text(text: str) -> SyntaxTree:
    return SyntaxTree.fromText(text)


def text_uses_default_nettype_none(text: str) -> bool:
    return bool(DEFAULT_NETTYPE_NONE_RE.search(text))


def file_uses_default_nettype_none(path: str) -> bool:
    return text_uses_default_nettype_none(Path(path).read_text(encoding="utf-8"))
