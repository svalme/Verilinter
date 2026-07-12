from .types import SyntaxTree


def parse_file(path: str) -> SyntaxTree:
    return SyntaxTree.fromFile(path)


def parse_text(text: str) -> SyntaxTree:
    return SyntaxTree.fromText(text)

