from typing import TYPE_CHECKING

from ...parser.syntax import is_task_declaration_node
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoTaskDeclarationRule(Rule):
    code = "NO_TASK_DECLARATION"
    message = "Use of task declarations is discouraged in synthesizable RTL"

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_task_declaration_node(vnode.raw)
