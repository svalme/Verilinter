from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .parameter_override import ParameterOverride
from .port_connection import PortConnection


@dataclass
class InstanceRecord(Mapping[str, Any]):
    """Represents a hierarchical module instance record registered during AST walk.

    Maintains connections, parameter overrides, location, and branch exclusivity
    metadata. Supports both strongly-typed attribute access and dictionary-style
    subscripting for backward compatibility.
    """

    parent_module: str | None = None
    child_module: str | None = None
    instance_name: str | None = None
    location: dict[str, Any] | None = None
    connection_style: str = "empty"
    connections: list[PortConnection] = field(default_factory=list)
    parameter_override_style: str = "none"
    parameter_overrides: list[ParameterOverride] = field(default_factory=list)
    generate_branch_signature: tuple[Any, ...] = ()

    _FIELDS = (
        "parent_module",
        "child_module",
        "instance_name",
        "location",
        "connection_style",
        "connections",
        "parameter_override_style",
        "parameter_overrides",
        "generate_branch_signature",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "parent_module": self.parent_module,
            "child_module": self.child_module,
            "instance_name": self.instance_name,
            "location": dict(self.location) if self.location is not None else None,
            "connection_style": self.connection_style,
            "connections": [c.to_dict() for c in self.connections],
            "parameter_override_style": self.parameter_override_style,
            "parameter_overrides": [p.to_dict() for p in self.parameter_overrides],
            "generate_branch_signature": self.generate_branch_signature,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | InstanceRecord) -> InstanceRecord:
        if isinstance(data, InstanceRecord):
            return data

        raw_conns = data.get("connections", [])
        connections = [
            c if isinstance(c, PortConnection) else PortConnection.from_dict(c)
            for c in (raw_conns if isinstance(raw_conns, Sequence) else [])
        ]

        raw_overrides = data.get("parameter_overrides", [])
        overrides = [
            p if isinstance(p, ParameterOverride) else ParameterOverride.from_dict(p)
            for p in (raw_overrides if isinstance(raw_overrides, Sequence) else [])
        ]

        raw_sig = data.get("generate_branch_signature", ())
        if isinstance(raw_sig, (list, tuple)):
            # Deep convert lists to tuples if needed
            def _to_tuple(item: Any, depth: int = 0) -> Any:
                if depth >= 32:
                    return ()
                if isinstance(item, (list, tuple)):
                    return tuple(_to_tuple(x, depth + 1) for x in item)
                return item

            sig = tuple(_to_tuple(x) for x in raw_sig)
        else:
            sig = ()

        raw_loc = data.get("location")
        loc = dict(raw_loc) if raw_loc is not None else None

        return cls(
            parent_module=data.get("parent_module"),
            child_module=data.get("child_module"),
            instance_name=data.get("instance_name"),
            location=loc,
            connection_style=str(data.get("connection_style", "empty")),
            connections=connections,
            parameter_override_style=str(data.get("parameter_override_style", "none")),
            parameter_overrides=overrides,
            generate_branch_signature=sig,
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
