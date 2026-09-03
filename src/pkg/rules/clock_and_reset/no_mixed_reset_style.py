from typing import Any

from ..base_symbol_rule import BaseSymbolRule
from ...semantic.symbol_table import SymbolTable
from ...vnodes.base_vnode import Location
from ..symbol_rule_runner import symbol_rule_runner


@symbol_rule_runner.register
class NoMixedResetStyleRule(BaseSymbolRule):
    code = "NO_MIXED_RESET_STYLE"
    category = "semantic_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        by_module: dict[str, list[tuple[str, Location]]] = {}
        for module_name, style, location in symbol_table.reset_style_events:
            by_module.setdefault(module_name, []).append((style, location))

        for module_name, events in by_module.items():
            first_style: str | None = None
            for style, location in events:
                if first_style is None:
                    first_style = style
                    continue
                if style != first_style:
                    diagnostic = {
                        "code": self.code,
                        "line": location["line"],
                        "col": location["col"],
                        "message": (
                            f"Module '{module_name}' mixes synchronous- and asynchronous-reset-style "
                            f"procedural blocks in the same module"
                        ),
                    }
                    if "file" in location:
                        diagnostic["file"] = location["file"]
                    diagnostics.append(diagnostic)
                    break

        return diagnostics
