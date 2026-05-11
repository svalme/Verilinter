from abc import ABC
from typing import Any

from ..vnodes.base_vnode import BaseVNode


class BaseDiagnostic(ABC):
    code: str = "UNSPEC"
    message: str = "No message"

    def report(self, vnode: BaseVNode) -> dict[str, Any]:
        return {
            "line": vnode.location["line"],
            "col": vnode.location["col"],
            "message": self.message,
        }
