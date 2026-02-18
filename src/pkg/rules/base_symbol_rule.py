from typing import Any
from ..vnodes.base_vnode import BaseVNode
from ..ast.symbol_table import SymbolTable

class BaseSymbolRule:
    """Base class for all linting rules."""
    code: str = "UNSPEC"
    message: str = "No message"

    def report(self, vnode: BaseVNode) -> dict[str, Any]:
        """Generate a diagnostic report for the violation."""
        return {
            "line": vnode.location["line"],
            "col": vnode.location["col"],
            "message": self.message
        }
    
    def run(self, symbol_table: SymbolTable) -> list[dict]:
        return []