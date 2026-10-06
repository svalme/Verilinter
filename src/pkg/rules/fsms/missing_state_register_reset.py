from typing import TYPE_CHECKING

from ...parser.syntax import (
    classify_reset_style,
    is_case_statement,
    state_machine_model,
)
from ...parser.types import CaseStatementNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


def _is_missing_state_register_reset(vnode: BaseVNode, ctx: "Context") -> bool:
    if not is_case_statement(vnode.raw):
        return False
    model = state_machine_model(vnode.raw, ctx)
    if model is None:
        return False

    if classify_reset_style(model.sequential_block) != "async":
        return False

    return not model.reset_covered


@rule_runner.register
class MissingStateRegisterResetRule(Rule):
    """Flags a state-register case statement in an async-reset-classified
    procedural block where the state register is never assigned inside the
    reset-asserted conditional -- its post-reset value is undefined.

    Deliberately async-only: a sync-reset block's reset signal has no
    structural marker distinguishing it from any other identifier, the same
    restraint `ASYNC_RESET_XZ_VALUE`/`RESET_SIGNAL_NAMING` already document.
    """

    code = "MISSING_STATE_REGISTER_RESET"
    message = "State register is not assigned inside the reset branch; its post-reset value is undefined"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    target_node_types = (CaseStatementNode,)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return _is_missing_state_register_reset(vnode, ctx)
