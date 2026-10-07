from typing import TYPE_CHECKING

from ...parser.syntax import (
    enclosing_case_statement,
    has_default_case_item,
    is_endcase_token,
    is_state_register_case,
)
from ...parser.types import Token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class MissingDefaultOnStateCaseRule(Rule):
    """State-register-aware sibling of `NO_DEFAULT_CASE_STATEMENT`: a missing
    default in an ordinary mux is a style nit, but in a state machine it can
    synthesize an inferred latch or leave the FSM's behavior on an
    out-of-range state value entirely undefined. Always co-fires with
    `NO_DEFAULT_CASE_STATEMENT` on the same construct -- see `overlaps_with`
    and the matching regression case in `tests/rules/overlap/test_rule_overlap_harness.py`.
    """

    code = "MISSING_DEFAULT_ON_STATE_CASE"
    message = "State case statement missing default case"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    overlaps_with = ("NO_DEFAULT_CASE_STATEMENT",)
    target_node_types = (Token,)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        if not is_endcase_token(vnode.raw):
            return False

        case_statement = enclosing_case_statement(ctx)
        if case_statement is None:
            return False

        if not is_state_register_case(case_statement.raw, ctx):
            return False

        return not has_default_case_item(case_statement.raw)
