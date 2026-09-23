from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PortConnection(Mapping[str, Any]):
    """Represents a single port connection within a hierarchical module instantiation.

    Supports both strongly-typed attribute access (`conn.port_name`, `conn.kind`)
    and dictionary-style subscripting (`conn["port_name"]`, `conn.get("port_name")`)
    for seamless compatibility with existing rules and tests.
    """

    kind: str  # "named", "ordered", "wildcard", "empty"
    location: dict[str, Any] | None = None
    port_name: str | None = None
    expr_text: str | None = None
    expr_name: str | None = None
    expr_width: int | None = None
    expr_signed: bool | None = None

    _FIELDS = (
        "kind",
        "location",
        "port_name",
        "expr_text",
        "expr_name",
        "expr_width",
        "expr_signed",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "location": dict(self.location) if self.location is not None else None,
            "port_name": self.port_name,
            "expr_text": self.expr_text,
            "expr_name": self.expr_name,
            "expr_width": self.expr_width,
            "expr_signed": self.expr_signed,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | PortConnection) -> PortConnection:
        if isinstance(data, PortConnection):
            return data
        raw_loc = data.get("location")
        loc = dict(raw_loc) if raw_loc is not None else None
        return cls(
            kind=str(data.get("kind", "empty")),
            location=loc,
            port_name=data.get("port_name"),
            expr_text=data.get("expr_text"),
            expr_name=data.get("expr_name"),
            expr_width=data.get("expr_width"),
            expr_signed=data.get("expr_signed"),
        )

    def __getitem__(self, key: str) -> Any:
        if key in self._FIELDS:
            return getattr(self, key)
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return iter(self._FIELDS)

    def __len__(self) -> int:
        return len(self._FIELDS)

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._FIELDS:
            val = getattr(self, key)
            return default if val is None and default is not None else val
        return default

    def __contains__(self, key: object) -> bool:
        return key in self._FIELDS
