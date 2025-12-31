import re

BLOCKING_RE = re.compile(r'(?<!<)=(?!=)')

def has_blocking(snippet: str) -> bool:
    return bool(BLOCKING_RE.search(snippet))

def has_nonblocking(snippet: str) -> bool:
    return "<=" in snippet

def missing_default(snippet: str) -> bool:
    return "default" not in snippet
