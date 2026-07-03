from abc import abstractmethod

from ..vnodes.base_vnode import BaseVNode
from .base_diagnostic import BaseDiagnostic


class Rule(BaseDiagnostic):

    @abstractmethod
    def applies(self, vnode: BaseVNode, ctx) -> bool: ...