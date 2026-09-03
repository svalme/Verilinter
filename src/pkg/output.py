from __future__ import annotations

import json
from typing import Any

from .diagnostics import Diagnostic, metadata_by_code
from .rules.connection_analysis import (
    duplicate_named_port_names,
    has_ordered_parameter_overrides,
    has_ordered_port_connections,
    has_wildcard_port_connections,
    unknown_named_port_names,
    unread_instance_output_details,
    unconnected_port_names,
    width_mismatch_details,
    width_unknown_details,
)
from .semantic.symbol_table import SymbolTable


def format_text(diagnostics: list[Diagnostic]) -> str:
    if not diagnostics:
        return "No issues found.\n"

    lines: list[str] = []
    for diagnostic in diagnostics:
        file_prefix = f"{diagnostic['file']}:" if diagnostic.get("file") else ""
        severity = diagnostic.get("severity", "warning").upper()
        lines.append(
            f"{file_prefix}{diagnostic['line']}:{diagnostic['col']} - "
            f"[{diagnostic['code']}] [{severity}] {diagnostic['message']}"
        )
    return "\n".join(lines) + "\n"


def format_json(diagnostics: list[Diagnostic]) -> str:
    return json.dumps(diagnostics, indent=2) + "\n"


def _sarif_level(severity: str) -> str:
    return {
        "error": "error",
        "warning": "warning",
        "info": "note",
    }.get(severity, "warning")


def format_sarif(diagnostics: list[Diagnostic]) -> str:
    metadata = metadata_by_code()
    rules = [
        {
            "id": code,
            "name": code,
            "shortDescription": {"text": item.message},
            "properties": {
                "category": item.category,
                "defaultSeverity": item.default_severity,
            },
        }
        for code, item in sorted(metadata.items())
    ]

    results: list[dict[str, Any]] = []
    for diagnostic in diagnostics:
        result = {
            "ruleId": diagnostic["code"],
            "level": _sarif_level(str(diagnostic.get("severity", "warning"))),
            "message": {"text": diagnostic["message"]},
            "properties": {
                "category": diagnostic.get("category"),
                "severity": diagnostic.get("severity"),
            },
        }
        if diagnostic.get("file"):
            result["locations"] = [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": str(diagnostic["file"])},
                        "region": {
                            "startLine": int(diagnostic.get("line", 0)),
                            "startColumn": int(diagnostic.get("col", 0)),
                        },
                    }
                }
            ]
        results.append(result)

    payload = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Verilinter",
                        "informationUri": "https://github.com/",
                        "rules": rules,
                    }
                },
                "results": results,
            }
        ],
    }
    return json.dumps(payload, indent=2) + "\n"


def render_diagnostics(diagnostics: list[Diagnostic], fmt: str) -> str:
    if fmt == "text":
        return format_text(diagnostics)
    if fmt == "json":
        return format_json(diagnostics)
    if fmt == "sarif":
        return format_sarif(diagnostics)
    raise ValueError(f"unknown output format '{fmt}'")


def render_connection_report(symbol_table: SymbolTable) -> str:
    lines: list[str] = []
    lines.append("Module Connection Summary")

    module_ports: dict[str, list[Any]] = {}
    for name, scopes in symbol_table.modules.items():
        if not scopes:
            continue
        scope = scopes[0]
        module_ports[name] = [symbol for symbol in scope.symbols.values() if symbol.is_port]

    if not symbol_table.instantiations:
        lines.append("No instantiations found.")
        return "\n".join(lines) + "\n"

    for inst in sorted(
        symbol_table.instantiations,
        key=lambda item: (
            str(item.get("parent_module") or ""),
            str(item.get("child_module") or ""),
            str(item.get("instance_name") or ""),
        ),
    ):
        parent = str(inst.get("parent_module") or "<unknown>")
        child = str(inst.get("child_module") or "<unknown>")
        instance_name = str(inst.get("instance_name") or "<unnamed>")
        style = str(inst.get("connection_style") or "empty")
        lines.append(f"{parent} -> {child} ({instance_name}) [{style}]")

        child_port_list = module_ports.get(child, [])
        named_ports = {conn.get("port_name"): conn for conn in inst.get("connections", []) if conn.get("kind") == "named"}
        ordered_connections = [conn for conn in inst.get("connections", []) if conn.get("kind") in {"ordered", "empty"}]
        wildcard_present = has_wildcard_port_connections(inst)

        if wildcard_present:
            lines.append("  <wildcard port binding: explicit per-port mapping not expanded>")
        elif style == "named":
            for port in child_port_list:
                conn = named_ports.get(port.name)
                if conn is None:
                    lines.append(f"  {port.name}: <unconnected>")
                    continue
                lines.append(f"  {port.name}: {conn.get('expr_text') or '<open>'}")
        elif style in {"ordered", "mixed"}:
            for index, port in enumerate(child_port_list):
                conn = ordered_connections[index] if index < len(ordered_connections) else None
                if conn is None or conn.get("kind") == "empty":
                    lines.append(f"  {port.name}: <unconnected>")
                    continue
                lines.append(f"  {port.name}: {conn.get('expr_text') or '<open>'}")

        issues: list[str] = []
        if wildcard_present:
            issues.append("uses wildcard port connections")
        if style == "mixed":
            issues.append("mixes named and ordered connections")
        if has_ordered_port_connections(inst):
            issues.append("uses ordered port connections")
        if has_ordered_parameter_overrides(inst):
            issues.append("uses ordered parameter overrides")
        for name in duplicate_named_port_names(inst):
            issues.append(f"duplicate named port {name}")
        for name in unknown_named_port_names(symbol_table, inst):
            issues.append(f"unknown child port {name}")
        for name in unconnected_port_names(symbol_table, inst):
            issues.append(f"unconnected port {name}")
        for port_name, port_width, expr_text, expr_width in width_mismatch_details(symbol_table, inst):
            issues.append(f"width mismatch on {port_name}: port {port_width}, expr {expr_width} ({expr_text})")
        for port_name, port_width, expr_text, expr_width in width_unknown_details(symbol_table, inst):
            issues.append(
                f"cannot infer width on {port_name}: "
                f"port {port_width if port_width is not None else 'unknown'}, "
                f"expr {expr_width if expr_width is not None else 'unknown'} ({expr_text})"
            )
        for port_name, signal_name in unread_instance_output_details(symbol_table, inst):
            issues.append(f"output {port_name} appears unread via {signal_name}")

        if issues:
            lines.append(f"  issues: {', '.join(issues)}")

    return "\n".join(lines) + "\n"
