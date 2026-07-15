from abc import abstractmethod
from typing import TYPE_CHECKING

from ..vnodes.base_vnode import BaseVNode
from .base_diagnostic import BaseDiagnostic

if TYPE_CHECKING:
    from ..walk.context import Context


class Rule(BaseDiagnostic):
    @abstractmethod
    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool: ...
