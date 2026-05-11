from ..vnodes.base_vnode import BaseVNode
from .base_diagnostic import BaseDiagnostic


class Rule(BaseDiagnostic):

    def applies(self, vnode: BaseVNode, ctx) -> bool | None:
        return None