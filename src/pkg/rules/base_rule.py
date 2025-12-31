from ..vnode.base_vnode import BaseVNode
from ..ast.symbol_table import SymbolTable

class Rule:
    """Base class for all linting rules."""
    code: str = "UNSPEC"
    message: str = "No message"

    def applies(self, vnode: BaseVNode, ctx) -> bool:
        """Determine if this rule applies to the given vnode and context."""
        pass

    def report(self, vnode: BaseVNode) -> dict[str, any]:
        """Generate a diagnostic report for the violation."""
        return {
            "line": vnode.location["line"],
            "col": vnode.location["col"],
            "message": self.message
        }
    
    def run(self, symbol_table: SymbolTable):
        pass