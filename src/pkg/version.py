"""Tool version for reports: the installed distribution, else the checkout's pyproject.toml."""
from __future__ import annotations

from importlib import metadata
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib  # type: ignore[no-redef]


def tool_version() -> str:
    try:
        return metadata.version("verilinter")
    except metadata.PackageNotFoundError:
        pass
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    try:
        return str(tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"])
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        return "unknown"
