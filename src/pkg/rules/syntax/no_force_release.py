from typing import TYPE_CHECKING

from ...parser.syntax import is_force_release_token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoForceReleaseRule(Rule):
    code = "NO_FORCE_RELEASE"
    message = "Use of force/release is discouraged in RTL; prefer explicit structural or procedural intent"

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_force_release_token(vnode.raw)
