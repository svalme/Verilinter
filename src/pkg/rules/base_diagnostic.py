from abc import ABC
from typing import Any

from ..vnodes.base_vnode import BaseVNode


class BaseDiagnostic(ABC):
    code: str = "UNSPEC"
    message: str = "No message"

    def report(self, vnode: BaseVNode) -> dict[str, Any]:
        diagnostic: dict[str, Any] = {
            "code": self.code,
            "line": vnode.location["line"],
            "col": vnode.location["col"],
            "message": self.message,
        }
        if "file" in vnode.location:
            diagnostic["file"] = vnode.location["file"]
        return diagnostic
