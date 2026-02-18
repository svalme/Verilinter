# src/pkg/vnode/token_vnode.py

import pyslang as sl
from .base_vnode import BaseVNode, Location

class TokenVNode(BaseVNode):

    def __init__(self, raw: sl.Token, tree: sl.SyntaxTree):
        self.raw = raw
        self.tree = tree

    @property
    def location(self) -> Location:
        loc: sl.SourceLocation = self.raw.location
        if not loc:
            return {"line": 0, "col": 0}

        sm: sl.SourceManager = self.tree.sourceManager
        return {"line": sm.getLineNumber(loc),
                "col": sm.getColumnNumber(loc)}
    
    def snippet(self) -> str:
        return self.raw.rawText
    
    def __repr__(self) -> str:
        loc = self.location
        loc_str = f"{loc['line']}:{loc['col']}" if loc else "?:?"
        return f"TokenVNode {self.raw.kind.name} '{self.raw.rawText}' @ {loc_str}"


