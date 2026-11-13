from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..symbol import Symbol
    from .instance_record import InstanceRecord
    from .port_connection import PortConnection


@dataclass(frozen=True)
class ConnectionRecord:
    """One port of an instance and what is connected to it, resolved once the child module is known.

    `port` is the child's port symbol with its width re-evaluated under the instance's parameter overrides
    (`port_width`, `port_signed` read from it); it is None when the child module is unknown or the
    connection names a port the child does not have. `connection` is None for a port the instance leaves
    off its list. `signal` is the parent-module symbol a simple identifier connection names, found through
    the shared name lookup. `implicit` is True when the connection comes from `.*`. `child_known` is False when
    the child module is declared in no input file."""

    instance: InstanceRecord
    port_name: str | None
    direction: str | None
    port: Symbol | None
    connection: PortConnection | None
    signal: Symbol | None
    port_width: int | None
    port_signed: bool | None
    expr_width: int | None
    expr_signed: bool | None
    implicit: bool = False
    child_known: bool = True
