from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParameterOverride(Mapping[str, Any]):
    """Represents a parameter override (named or ordered) on an instantiation.

    Supports both strongly-typed attribute access (`override.param_name`, `override.kind`)
    and dictionary-style subscripting (`override["param_name"]`, `override.get("param_name")`)
    for seamless compatibility.
    """

    kind: str  # "named", "ordered"
    location: dict[str, Any] = field(default_factory=lambda: {"line": 0, "col": 0})
    param_name: str | None = None
    expr_text: str | None = None
    expr_value: int | None = None

    _FIELDS = ("kind", "location", "param_name", "expr_text", "expr_value")

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "location": dict(self.location),
            "param_name": self.param_name,
            "expr_text": self.expr_text,
            "expr_value": self.expr_value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | ParameterOverride) -> ParameterOverride:
        if isinstance(data, ParameterOverride):
            return data
        return cls(
            kind=str(data.get("kind", "ordered")),
            location=dict(data.get("location", {"line": 0, "col": 0})),
            param_name=data.get("param_name"),
            expr_text=data.get("expr_text"),
            expr_value=data.get("expr_value") if isinstance(data.get("expr_value"), int) else None,
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
