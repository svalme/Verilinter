from typing import Any
from ..vnodes.base_vnode import BaseVNode
from ..ast.symbol_table import SymbolTable

class Rule:
    """Base class for all linting rules."""
    code: str = "UNSPEC"
    message: str = "No message"

    def applies(self, vnode: BaseVNode, ctx) -> bool | None:
        """Determine if this rule applies to the given vnode and context.

        By default, rules do not state applicability (return None).
        Concrete rules should return True/False explicitly.
        """
        return None

    def report(self, vnode: BaseVNode) -> dict[str, Any]:
        """Generate a diagnostic report for the violation."""
        return {
            "line": vnode.location["line"],
            "col": vnode.location["col"],
            "message": self.message
        }
    
    def run(self, symbol_table: SymbolTable):
        pass