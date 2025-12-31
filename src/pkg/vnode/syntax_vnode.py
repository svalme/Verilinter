import pyslang as sl

from .base_vnode import BaseVNode, Location

class SyntaxVNode(BaseVNode):

    def __init__(self, raw: sl.SyntaxNode, tree: sl.SyntaxTree):
        self.raw = raw
        self.tree = tree

    @property
    def location(self) -> Location | None:
        sr: sl.SourceRange | None = self.raw.sourceRange

        if not sr or not sr.start:
            return None

        sm: sl.SourceManager = self.tree.sourceManager
        return {"line": sm.getLineNumber(sr.start),
                "col": sm.getColumnNumber(sr.start)}
    
    def snippet(self) -> str:
        return self.raw.__str__()
        
    def __repr__(self) -> str:
        loc = self.location
        loc_str = f"{loc['line']}:{loc['col']}" if loc else "?:?"
        return f"SyntaxVNode {self.raw.kind.name} @ {loc_str}"
    
    @property
    def children(self) -> list[sl.SyntaxNode | sl.Token]:
        return list(self.raw.__iter__())
              
