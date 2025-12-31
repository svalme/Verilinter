import pyslang as sl
from ..ast.context import Context
from ..vnode.base_vnode import BaseVNode


def is_clocked_block(vnode: BaseVNode) -> bool:
    raw = vnode.raw

    if not isinstance(raw, sl.ProceduralBlockSyntax):
        return False

    timing = raw.timing
    if timing is None:
        return False

    for item in timing:
        if item.kind.name in ("PosedgeEvent", "NegedgeEvent"):
            return True

    return False


def in_sequential_block(ctx: Context) -> bool:
    return any(
        is_clocked_block(vnode)
        for vnode in ctx.stack
    )
