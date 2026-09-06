import re

_LOWER_SNAKE_CASE_RE = re.compile(r"[a-z][a-z0-9_]*$")
_UPPER_SNAKE_CASE_RE = re.compile(r"[A-Z][A-Z0-9_]*$")


def is_lower_snake_case(name: str) -> bool:
    return bool(_LOWER_SNAKE_CASE_RE.match(name))


def is_upper_snake_case(name: str) -> bool:
    return bool(_UPPER_SNAKE_CASE_RE.match(name))
