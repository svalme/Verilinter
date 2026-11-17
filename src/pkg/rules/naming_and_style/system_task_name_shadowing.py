from typing import TYPE_CHECKING

from ...parser.syntax import ALL_SYSTEM_TASK_NAMES, declarator_name, subroutine_name
from ...parser.types import DeclaratorNode, FunctionDeclarationNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class SystemTaskNameShadowingRule(Rule):
    """A naming convention: a declared name (a variable, net, function or task) that equals a system task or
    function name without its `$` (`display`, `finish`, `random`) is easy to confuse with that system task at a
    call site. Nothing is hidden, since a system task has its own namespace (`$display` and `display` are different
    names), so the finding makes no claim about behavior."""

    code = "SYSTEM_TASK_NAME_SHADOWING"
    message = "Name matches a built-in system task or function name without its '$', which is easy to confuse with it"
    category = "rtl_style"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    target_node_types = (DeclaratorNode, FunctionDeclarationNode)

    def applies(self, vnode: BaseVNode, _ctx: "Context") -> bool:
        raw = vnode.raw
        if isinstance(raw, DeclaratorNode):
            name = declarator_name(raw)
        elif isinstance(raw, FunctionDeclarationNode):  # a task declaration is parsed as the same node type
            name = subroutine_name(raw)
        else:
            return False
        return name is not None and name in ALL_SYSTEM_TASK_NAMES
