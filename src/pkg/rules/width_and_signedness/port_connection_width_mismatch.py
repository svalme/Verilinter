from typing import Any

from ...semantic.symbol_table import SymbolTable
from ..base_symbol_rule import BaseSymbolRule
from ..connection_analysis import (
    signedness_mismatch_details,
    width_mismatch_details,
    width_unknown_details,
)
from ..module_rule_runner import module_rule_runner


@module_rule_runner.register
class PortConnectionWidthMismatchRule(BaseSymbolRule):
    code = "PORT_CONNECTION_WIDTH_MISMATCH"
    category = "module_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        for inst in symbol_table.instantiations:
            loc = dict(inst.get("location") or {})
            for port_name, port_width, expr_text, expr_width in width_mismatch_details(symbol_table, inst):
                diagnostics.append(
                    {
                        "code": self.code,
                        "line": loc.get("line", 0),
                        "col": loc.get("col", 0),
                        "file": loc.get("file"),
                        "message": (
                            f"Instance '{inst.get('instance_name')}' connects port '{port_name}' "
                            f"width {port_width} to '{expr_text}' width {expr_width}"
                        ),
                    }
                )
        return diagnostics


@module_rule_runner.register
class PortConnectionWidthUnknownRule(BaseSymbolRule):
    code = "PORT_CONNECTION_WIDTH_UNKNOWN"
    category = "module_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        for inst in symbol_table.instantiations:
            loc = dict(inst.get("location") or {})
            for port_name, port_width, expr_text, expr_width in width_unknown_details(symbol_table, inst):
                diagnostics.append(
                    {
                        "code": self.code,
                        "line": loc.get("line", 0),
                        "col": loc.get("col", 0),
                        "file": loc.get("file"),
                        "message": (
                            f"Cannot infer width confidently for instance '{inst.get('instance_name')}' "
                            f"port '{port_name}' ({'known width ' + str(port_width) if port_width is not None else 'unknown port width'}) "
                            f"connected to '{expr_text}' ({'known width ' + str(expr_width) if expr_width is not None else 'unknown expression width'})"
                        ),
                    }
                )
        return diagnostics


@module_rule_runner.register
class PortConnectionSignednessMismatchRule(BaseSymbolRule):
    code = "PORT_CONNECTION_SIGNEDNESS_MISMATCH"
    category = "module_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []
        for inst in symbol_table.instantiations:
            loc = dict(inst.get("location") or {})
            for port_name, port_signed, expr_text, expr_signed in signedness_mismatch_details(
                symbol_table, inst
            ):
                diagnostics.append(
                    {
                        "code": self.code,
                        "line": loc.get("line", 0),
                        "col": loc.get("col", 0),
                        "file": loc.get("file"),
                        "message": (
                            f"Instance '{inst.get('instance_name')}' connects port '{port_name}' "
                            f"({'signed' if port_signed else 'unsigned'}) to '{expr_text}' "
                            f"({'signed' if expr_signed else 'unsigned'})"
                        ),
                    }
                )
        return diagnostics
