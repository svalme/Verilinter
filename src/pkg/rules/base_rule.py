from abc import abstractmethod
from typing import TYPE_CHECKING

from ..vnodes.base_vnode import BaseVNode
from .base_diagnostic import BaseDiagnostic

if TYPE_CHECKING:
    from ..walk.context import Context


class Rule(BaseDiagnostic):
    target_node_types: tuple[type, ...] | None = None
    # True for a rule whose finding depends on parameter values: it is dropped when the reported node sits
    # in a generate branch that the default parameter values switch off (`in_inactive_generate_branch`).
    skip_in_inactive_generate_branch: bool = False

    @abstractmethod
    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool: ...

