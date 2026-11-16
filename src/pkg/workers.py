"""The per-file workers: parse, walk and rule runs for one file, in-process or in a process pool, and the result record each returns."""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence
from .parser.parse import extract_header_dependencies, extract_parse_diagnostics, file_uses_default_nettype_none, parse_file
from .parser.traversal_guard import collect_truncations
from .rules.register_rules import *
from .rules.register_rules import rule_runner, symbol_rule_runner
from .rules.rule_selection import RuleSelection
from .semantic.models import InstanceRecord
from .semantic.instance_effects import apply_instance_port_effects, release_walk_state
from .semantic.module_registry import seed_cross_file_module_ports
from .semantic.package_registry import seed_cross_file_packages
from .semantic.symbol_serialization import symbol_to_dict
from .semantic.symbol_table import SymbolTable
from .walk.context import Context
from .walk.dispatch import dispatch
from .walk.walker import Walker
from .handlers.register_handlers import *
from .vnodes.register_vnodes import *
import inspect
import sys


def get_override(attr: str, default: Any) -> Any:
    rl = sys.modules.get("src.run_lint")
    if rl is not None and hasattr(rl, attr):
        return getattr(rl, attr)
    return default


def call_parse_file(
    parse_fn: Any,
    path: str,
    include_dirs: list[str] | None = None,
    defines: Sequence[str] | None = None,
) -> Any:
    try:
        sig = inspect.signature(parse_fn)
        params = sig.parameters
        accepts_defines = "defines" in params or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
        accepts_include_dirs = "include_dirs" in params or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    except (ValueError, TypeError):
        accepts_defines = True
        accepts_include_dirs = True

    kwargs: dict[str, Any] = {}
    if accepts_include_dirs:
        kwargs["include_dirs"] = include_dirs
    if accepts_defines and defines is not None:
        kwargs["defines"] = defines
    elif accepts_defines:
        kwargs["defines"] = defines

    return parse_fn(path, **kwargs)


@dataclass(frozen=True)
class WorkerResult:
    diagnostics: list[dict[str, Any]]
    modules: list[dict[str, Any]]
    primitives: list[str]
    module_references: list[tuple[str, dict[str, Any]]]
    instantiation_edges: list[tuple[str, str, dict[str, Any]]]
    instantiations: list[InstanceRecord]
    header_dependencies: list[dict[str, str]] = field(default_factory=list)
    truncations: list[dict[str, Any]] = field(default_factory=list)


def lint_single_tree(
    file_name: str,
    tree: Any,
    rule_selection: RuleSelection | None = None,
    package_registry: dict[str, list[dict[str, Any]]] | None = None,
    default_nettype_none: bool = False,
    header_dependencies: list[dict[str, str]] | None = None,
    rule_runner_inst: Any = None,
    symbol_rule_runner_inst: Any = None,
    module_ports: dict[str, list[dict[str, Any]]] | None = None,
) -> WorkerResult:
    _Walker = get_override("Walker", Walker)
    _rule_runner = rule_runner_inst or get_override("rule_runner", rule_runner)
    _symbol_rule_runner = symbol_rule_runner_inst or get_override(
        "symbol_rule_runner", symbol_rule_runner
    )

    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = _Walker(dispatch)
    ast_diagnostics: list[dict[str, Any]] = []

    def on_node(vnode: object, node_ctx: object) -> None:
        ast_diagnostics.extend(_rule_runner.check(vnode, node_ctx, rule_selection))

    symbol_table.set_current_file(file_name)
    symbol_table.set_current_file_default_nettype_none(default_nettype_none)
    seed_cross_file_packages(symbol_table, package_registry, file_name)
    seed_cross_file_module_ports(symbol_table, module_ports, file_name)

    truncations: list[dict[str, Any]] = []
    with collect_truncations(file_name=file_name, tree=tree) as trunc_events:
        walker.walk(tree.root, tree, ctx, symbol_table, on_node=on_node)
        apply_instance_port_effects(symbol_table)
        release_walk_state(symbol_table)
        diagnostics = ast_diagnostics + _symbol_rule_runner.run(symbol_table, rule_selection)
        truncations = [e.to_dict() for e in trunc_events]

    modules: list[dict[str, Any]] = []
    for name, scopes in symbol_table.modules.items():
        for scope in scopes:
            symbols: list[dict[str, object]] = []
            for symbol in scope.symbols.values():
                symbols.append(symbol_to_dict(symbol))
            modules.append(
                {
                    "name": name,
                    "file": scope.file,
                    "location": scope.location,
                    "symbols": symbols,
                }
            )

    return WorkerResult(
        diagnostics=diagnostics,
        modules=modules,
        primitives=sorted(symbol_table.primitives),
        module_references=list(symbol_table.module_references),
        instantiation_edges=list(symbol_table.instantiation_edges),
        instantiations=list(symbol_table.instantiations),
        header_dependencies=header_dependencies or [],
        truncations=truncations,
    )


def _lint_single_file(
    path: str,
    rule_selection: RuleSelection | None,
    include_dirs: list[str] | None = None,
    package_registry: dict[str, list[dict[str, Any]]] | None = None,
    defines: Sequence[str] | None = None,
    rule_runner_inst: Any = None,
    symbol_rule_runner_inst: Any = None,
    module_ports: dict[str, list[dict[str, Any]]] | None = None,
) -> WorkerResult:
    _parse_file = get_override("parse_file", parse_file)
    _file_uses_default_nettype_none = get_override(
        "file_uses_default_nettype_none", file_uses_default_nettype_none
    )

    tree = call_parse_file(_parse_file, path, include_dirs=include_dirs, defines=defines)
    header_dependencies = extract_header_dependencies(tree)
    parse_errors = extract_parse_diagnostics(tree, path)
    if parse_errors:
        return WorkerResult(
            diagnostics=parse_errors,
            modules=[],
            primitives=[],
            module_references=[],
            instantiation_edges=[],
            instantiations=[],
            header_dependencies=header_dependencies,
        )

    return lint_single_tree(
        file_name=path,
        tree=tree,
        rule_selection=rule_selection,
        package_registry=package_registry,
        default_nettype_none=_file_uses_default_nettype_none(path),
        header_dependencies=header_dependencies,
        rule_runner_inst=rule_runner_inst,
        symbol_rule_runner_inst=symbol_rule_runner_inst,
        module_ports=module_ports,
    )


def run_workers(
    paths: list[Path],
    jobs: int,
    rule_selection: RuleSelection | None,
    include_dirs: list[str] | None = None,
    package_registry: dict[str, list[dict[str, Any]]] | None = None,
    defines: Sequence[str] | None = None,
    rule_runner_inst: Any = None,
    symbol_rule_runner_inst: Any = None,
    module_ports: dict[str, list[dict[str, Any]]] | None = None,
) -> list[WorkerResult]:
    ordered_paths = [str(path) for path in paths]

    if jobs == 1 or rule_runner_inst is not None or symbol_rule_runner_inst is not None:
        return [
            _lint_single_file(
                path,
                rule_selection,
                include_dirs,
                package_registry,
                defines,
                rule_runner_inst=rule_runner_inst,
                symbol_rule_runner_inst=symbol_rule_runner_inst,
                module_ports=module_ports,
            )
            for path in ordered_paths
        ]

    try:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            return list(
                pool.map(
                    _lint_single_file,
                    ordered_paths,
                    [rule_selection] * len(ordered_paths),
                    [include_dirs] * len(ordered_paths),
                    [package_registry] * len(ordered_paths),
                    [defines] * len(ordered_paths),
                    [None] * len(ordered_paths),
                    [None] * len(ordered_paths),
                    [module_ports] * len(ordered_paths),
                )
            )
    except (OSError, PermissionError):
        return [
            _lint_single_file(path, rule_selection, include_dirs, package_registry, defines, module_ports=module_ports)
            for path in ordered_paths
        ]


def worker_result_from_payload(payload: dict[str, Any]) -> WorkerResult:
    return WorkerResult(
        diagnostics=list(payload.get("diagnostics", [])),
        modules=list(payload.get("modules", [])),
        primitives=list(payload.get("primitives", [])),
        module_references=list(payload.get("module_references", [])),
        instantiation_edges=list(payload.get("instantiation_edges", [])),
        instantiations=[
            InstanceRecord.from_dict(inst) if isinstance(inst, dict) else inst
            for inst in payload.get("instantiations", [])
        ],
        header_dependencies=list(payload.get("header_dependencies", [])),
        truncations=list(payload.get("truncations", [])),
    )


def warn_store_unavailable(store_path: Path, exc: Exception) -> None:
    print(
        f"warning: analysis store {store_path} is unusable ({exc}); continuing without the cache",
        file=sys.stderr,
    )
