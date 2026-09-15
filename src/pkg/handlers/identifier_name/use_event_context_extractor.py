from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ...parser.syntax import (
    NONBLOCKING_ASSIGNMENT_KIND,
    branch_exclusivity_signature,
    enclosing_assignment_expression,
    enclosing_continuous_assign,
    enclosing_for_loop_ids,
    enclosing_port_connection,
    enclosing_procedural_block,
    identifier_access_modes,
    is_combinational_driver_block,
    is_continuous_assign,
    is_system_task_output_argument,
    is_tristate_continuous_assign,
    subroutine_formal_direction,
)

if TYPE_CHECKING:
    from ...semantic.symbol_table import SymbolTable
    from ...vnodes.identifier_vnode import IdentifierNameVNode
    from ...walk.context import Context


@dataclass(frozen=True)
class UseEventContext:
    """Rich syntactic and semantic context accompanying an identifier use event."""

    is_read: bool
    is_write: bool
    driver_id: str | None
    driver_location: dict[str, Any] | None
    branch_signature: tuple[tuple[str, int], ...] | None
    statement_id: str | None
    in_port_connection: bool
    is_nonblocking_write: bool
    loop_ids: tuple[str, ...]

    def to_use_kwargs(self) -> dict[str, Any]:
        """Convert to keyword arguments expected by `Symbol.add_use`."""
        return {
            "read": self.is_read,
            "write": self.is_write,
            "driver_id": self.driver_id,
            "driver_location": self.driver_location,
            "branch_signature": self.branch_signature,
            "statement_id": self.statement_id,
            "in_port_connection": self.in_port_connection,
            "is_nonblocking_write": self.is_nonblocking_write,
            "loop_ids": self.loop_ids,
        }


class UseEventContextExtractor:
    """Extracts execution and use-event context (access modes, driver block IDs,

    branch exclusivity, statement IDs, loop IDs) for an identifier reference.
    """

    def extract(
        self,
        vnode: IdentifierNameVNode,
        ctx: Context,
        symbol_table: SymbolTable,
    ) -> UseEventContext:
        is_read, is_write = identifier_access_modes(ctx, vnode.raw)
        if is_system_task_output_argument(vnode.raw):
            # `$readmemh(file, mem)`/`$value$plusargs(fmt, x)` populate this
            # argument rather than reading it, but identifier_access_modes has
            # no notion of a system-task argument at all and falls through to
            # a plain read.
            is_read, is_write = False, True
        else:
            subroutine_direction = subroutine_formal_direction(vnode.raw, symbol_table, ctx)
            if subroutine_direction == "output":
                is_read, is_write = False, True
            elif subroutine_direction in ("inout", "ref"):
                is_read, is_write = True, True
            elif subroutine_direction == "input":
                is_read, is_write = True, False

        driver_block = enclosing_procedural_block(ctx) or enclosing_continuous_assign(ctx)
        driver_id = None
        driver_location = None
        if driver_block is not None:
            loc = driver_block.location
            driver_id = (
                f"{driver_block.kind}:{loc.get('file', '')}:{loc['line']}:{loc['col']}"
            )
            driver_location = loc
            if is_write and is_combinational_driver_block(driver_block):
                symbol_table.mark_combinational_driver(driver_id)
            if is_write and is_continuous_assign(driver_block.raw) and is_tristate_continuous_assign(driver_block.raw):
                symbol_table.mark_tristate_driver(driver_id)

        branch_signature = branch_exclusivity_signature(vnode.raw, vnode.tree)

        assignment_node = enclosing_assignment_expression(ctx)
        statement_id = None
        if assignment_node is not None:
            stmt_loc = assignment_node.location
            statement_id = (
                f"stmt:{stmt_loc.get('file', '')}:{stmt_loc['line']}:{stmt_loc['col']}"
            )

        in_port_connection = enclosing_port_connection(ctx) is not None

        is_nonblocking_write = (
            is_write
            and assignment_node is not None
            and assignment_node.raw.kind == NONBLOCKING_ASSIGNMENT_KIND
        )

        loop_ids = enclosing_for_loop_ids(ctx)

        return UseEventContext(
            is_read=is_read,
            is_write=is_write,
            driver_id=driver_id,
            driver_location=driver_location,
            branch_signature=branch_signature,
            statement_id=statement_id,
            in_port_connection=in_port_connection,
            is_nonblocking_write=is_nonblocking_write,
            loop_ids=loop_ids,
        )
