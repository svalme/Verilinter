from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any
import pytest

from src.pkg.parser.parse import parse_text

from src.pkg.engine import (
    LintPipeline,
    WorkerResult,
    _symbol_from_dict,
    _symbol_to_dict,
    _worker_result_from_payload,
)
from src.pkg.semantic.symbol import Symbol, UseEvent
from src.pkg.rules.rule_runner import RuleRunner
from src.pkg.rules.rule_selection import RuleSelection
from src.pkg.rules.symbol_rule_runner import SymbolRuleRunner
from src.pkg.rules.module_rule_runner import ModuleRuleRunner
from src.pkg.rules.base_rule import Rule
from src.pkg.rules.base_symbol_rule import BaseSymbolRule
from src.pkg.semantic.models import InstanceRecord, PortConnection, ParameterOverride
from src.pkg.semantic.symbol_table import SymbolTable


class TestLintPipeline:
    def test_pipeline_isolates_worker_scopes(self) -> None:
        """Verify that per-file workers run in completely isolated SymbolTables."""
        file_inputs = [
            ("file_a.sv", parse_text("module mod_a;\n  logic [7:0] sig_a;\nendmodule\n")),
            ("file_b.sv", parse_text("module mod_b;\n  logic [7:0] sig_b;\nendmodule\n")),
        ]
        pipeline = LintPipeline()
        result = pipeline.analyze_trees(file_inputs)

        # Cross file symbol table has both modules
        assert "mod_a" in result.symbol_table.modules
        assert "mod_b" in result.symbol_table.modules

        scope_a = result.symbol_table.modules["mod_a"][0]
        scope_b = result.symbol_table.modules["mod_b"][0]

        # Scope A only knows about sig_a, Scope B only knows about sig_b
        assert "sig_a" in scope_a.symbols
        assert "sig_b" not in scope_a.symbols
        assert "sig_b" in scope_b.symbols
        assert "sig_a" not in scope_b.symbols

    def test_pipeline_cross_file_package_scanning_and_seeding(self) -> None:
        """Phase 1 package scanning discovers pkg in pkg.sv and seeds it for top.sv."""
        file_inputs = [
            (
                "pkg.sv",
                parse_text(
                    "package common_pkg;\n  parameter int DATA_WIDTH = 16;\nendpackage\n"
                ),
            ),
            (
                "top.sv",
                parse_text(
                    "module top;\n  import common_pkg::*;\n  logic [DATA_WIDTH-1:0] bus;\nendmodule\n"
                ),
            ),
        ]
        pipeline = LintPipeline()
        result = pipeline.analyze_trees(file_inputs)

        # No implicit net should be reported because DATA_WIDTH was seeded from common_pkg
        assert not any(d.get("code") == "NO_IMPLICIT_NET" for d in result.diagnostics)

    def test_pipeline_cross_file_module_rules_execution(self) -> None:
        """Phase 4 & 5 executes module rules (such as DUPLICATE_MODULE) across files."""
        file_inputs = [
            ("a.sv", parse_text("module duplicate_mod;\nendmodule\n")),
            ("b.sv", parse_text("module duplicate_mod;\nendmodule\n")),
        ]
        pipeline = LintPipeline()
        result = pipeline.analyze_trees(file_inputs)

        duplicate_diags = [d for d in result.diagnostics if d.get("code") == "DUPLICATE_MODULE"]
        assert len(duplicate_diags) == 1
        assert "duplicate_mod" in duplicate_diags[0]["message"]
        assert duplicate_diags[0]["file"] == "b.sv"

    def test_pipeline_worker_result_serialization_roundtrip(self) -> None:
        """Validate that all WorkerResult structures survive serialization and deserialization."""
        inst = InstanceRecord(
            parent_module="parent",
            child_module="child",
            instance_name="u_child",
            location={"file": "top.sv", "line": 10, "col": 5},
            connection_style="named",
            connections=[
                PortConnection(
                    kind="named",
                    location={"file": "top.sv", "line": 11, "col": 7},
                    port_name="clk",
                    expr_text="sys_clk",
                    expr_name="sys_clk",
                    expr_width=1,
                    expr_signed=False,
                )
            ],
            parameter_override_style="named",
            parameter_overrides=[
                ParameterOverride(
                    kind="named",
                    location={"file": "top.sv", "line": 10, "col": 15},
                    param_name="WIDTH",
                )
            ],
            generate_branch_signature=(("gen_if", 0),),
        )

        original = WorkerResult(
            diagnostics=[{"code": "TEST", "line": 1, "col": 1, "message": "msg", "file": "top.sv"}],
            modules=[
                {
                    "name": "parent",
                    "file": "top.sv",
                    "location": {"line": 1, "col": 1, "file": "top.sv"},
                    "symbols": [{"name": "sys_clk", "kind": "wire", "is_port": True}],
                }
            ],
            primitives=["udp_gate"],
            module_references=[("child", {"file": "top.sv", "line": 10, "col": 5})],
            instantiation_edges=[("parent", "child", {"file": "top.sv", "line": 10, "col": 5})],
            instantiations=[inst],
            header_dependencies=[{"include_name": "defs.svh", "resolved_path": "inc/defs.svh"}],
        )

        payload = asdict(original)
        deserialized = _worker_result_from_payload(payload)

        assert deserialized.diagnostics == original.diagnostics
        assert deserialized.modules == original.modules
        assert deserialized.primitives == original.primitives
        assert deserialized.module_references == original.module_references
        assert deserialized.instantiation_edges == original.instantiation_edges
        assert deserialized.header_dependencies == original.header_dependencies
        assert len(deserialized.instantiations) == 1

        deserialized_inst = deserialized.instantiations[0]
        assert isinstance(deserialized_inst, InstanceRecord)
        assert deserialized_inst.instance_name == "u_child"
        assert deserialized_inst.connections[0].port_name == "clk"
        assert deserialized_inst.parameter_overrides[0].param_name == "WIDTH"
        assert deserialized_inst.generate_branch_signature == (("gen_if", 0),)

    def test_symbol_use_event_roundtrip_preserves_all_fields(self) -> None:
        """`_symbol_to_dict`/`_symbol_from_dict` back the cross-file SymbolTable
        reconstruction (`_build_cross_file_symbol_table`) -- every `UseEvent`
        field must survive a real JSON round-trip (the SQLite cache path), not
        just the fields today's cross-file rules happen to read. The `keys()`
        assertion is the actual parity guarantee: if `UseEvent` ever gains a
        new field, this fixture (and the round-trip assertion below) must be
        updated to cover it, or this test fails first."""
        symbol = Symbol(name="sig", kind="variable")
        symbol.add_declaration({"line": 1, "col": 3, "file": "top.sv"})
        symbol.is_implicit = False
        symbol.is_port = True
        symbol.is_function_return = False
        symbol.port_direction = "output"
        symbol.bit_width = 16
        symbol.msb = 15
        symbol.lsb = 0
        symbol.is_signed = True
        symbol.value = 42
        symbol.is_constant = True
        symbol.is_localparam = True
        symbol.initializer_text = "16'sh002a"
        symbol.has_declaration_initializer = True
        symbol.is_event = False
        symbol.packed_dimensions = [("15", "0")]
        symbol.packed_dimension_widths = [16]
        symbol.unpacked_dimensions = [("0", "3")]
        symbol.unpacked_dimension_widths = [4]
        symbol.add_use(
            loc={"line": 3, "col": 5, "file": "top.sv"},
            read=True,
            write=True,
            driver_id="block:1",
            driver_location={"line": 2, "col": 1, "file": "top.sv"},
            branch_signature=(("if_stmt:1", 0), ("case_stmt:2", 1)),
            statement_id="stmt:1",
            in_port_connection=True,
            is_nonblocking_write=True,
            loop_ids=("loop:1", "loop:2"),
        )
        event = symbol.use_events[0]
        all_fields = UseEvent.__required_keys__ | UseEvent.__optional_keys__
        assert set(event.keys()) == all_fields, (
            "UseEvent gained/lost a field -- update this fixture's add_use(...) "
            "call to cover it before trusting the round-trip assertion below."
        )

        payload = json.loads(json.dumps(_symbol_to_dict(symbol)))
        restored = _symbol_from_dict(payload)

        assert restored.use_events == symbol.use_events
        expected_attrs = {k: v for k, v in symbol.__dict__.items() if k != "scope"}
        restored_attrs = {k: v for k, v in restored.__dict__.items() if k != "scope"}
        assert restored_attrs == expected_attrs
        assert restored.is_declared is True
        assert restored.is_explicit_kind("variable") is True

    def test_pipeline_custom_runners_injection(self) -> None:
        """Verify that custom rule runners (AST, symbol, module) can be injected into LintPipeline."""
        class CustomRule(Rule):
            code = "CUSTOM_AST"
            message = "custom ast violation"

            def applies(self, vnode: Any, ctx: Any) -> bool:
                return getattr(vnode, "identifier_name", None) == "flag_me"

        class CustomSymbolRule(BaseSymbolRule):
            code = "CUSTOM_SYM"
            message = "custom symbol violation"

            def run(self, symbol_table: SymbolTable, rule_selection: Any = None) -> list[dict[str, Any]]:
                return [{"code": self.code, "message": self.message, "line": 1, "col": 1, "file": "test.sv"}]

        class CustomModuleRule(BaseSymbolRule):
            code = "CUSTOM_MOD"
            message = "custom module violation"

            def run(self, symbol_table: SymbolTable, rule_selection: Any = None) -> list[dict[str, Any]]:
                return [{"code": self.code, "message": self.message, "line": 1, "col": 1, "file": "test.sv"}]

        custom_rule_runner = RuleRunner(rules=[CustomRule()])
        custom_symbol_runner = SymbolRuleRunner(rules=[CustomSymbolRule()])
        custom_module_runner = ModuleRuleRunner(rules=[CustomModuleRule()])

        pipeline = LintPipeline(
            rule_runner=custom_rule_runner,
            symbol_rule_runner=custom_symbol_runner,
            module_rule_runner=custom_module_runner,
        )

        file_inputs = [
            ("test.sv", parse_text("module test;\n  logic flag_me;\n  assign flag_me = 1'b0;\nendmodule\n")),
        ]
        result = pipeline.analyze_trees(file_inputs)

        codes = {d["code"] for d in result.diagnostics}
        assert "CUSTOM_AST" in codes
        assert "CUSTOM_SYM" in codes
        assert "CUSTOM_MOD" in codes

    def test_pipeline_custom_runners_injection_in_analyze_paths(self, tmp_path: Path) -> None:
        """Verify that injected custom runners are executed during analyze_paths."""
        src_file = tmp_path / "mod.sv"
        src_file.write_text("module mod;\n  logic flag_me;\n  assign flag_me = 1'b0;\nendmodule\n", encoding="utf-8")

        class CustomRule(Rule):
            code = "CUSTOM_PATH_AST"
            message = "custom path ast violation"

            def applies(self, vnode: Any, ctx: Any) -> bool:
                return getattr(vnode, "identifier_name", None) == "flag_me"

        class CustomSymbolRule(BaseSymbolRule):
            code = "CUSTOM_PATH_SYM"
            message = "custom path sym violation"

            def run(self, symbol_table: SymbolTable, rule_selection: Any = None) -> list[dict[str, Any]]:
                return [{"code": self.code, "message": self.message, "line": 1, "col": 1, "file": str(src_file)}]

        class CustomModuleRule(BaseSymbolRule):
            code = "CUSTOM_PATH_MOD"
            message = "custom path mod violation"

            def run(self, symbol_table: SymbolTable, rule_selection: Any = None) -> list[dict[str, Any]]:
                return [{"code": self.code, "message": self.message, "line": 1, "col": 1, "file": str(src_file)}]

        pipeline = LintPipeline(
            rule_runner=RuleRunner(rules=[CustomRule()]),
            symbol_rule_runner=SymbolRuleRunner(rules=[CustomSymbolRule()]),
            module_rule_runner=ModuleRuleRunner(rules=[CustomModuleRule()]),
        )

        result = pipeline.analyze_paths([src_file], jobs=1)
        codes = {d["code"] for d in result.diagnostics}
        assert "CUSTOM_PATH_AST" in codes
        assert "CUSTOM_PATH_SYM" in codes
        assert "CUSTOM_PATH_MOD" in codes

    def test_pipeline_custom_store_injection_in_analyze_paths(self, tmp_path: Path) -> None:
        """Verify that a custom or mock store can be injected into LintPipeline."""
        from unittest.mock import Mock
        from src.pkg.analysis_store import AnalysisStore

        src_file = tmp_path / "store_test.sv"
        src_file.write_text("module store_test;\nendmodule\n", encoding="utf-8")

        mock_store = Mock(spec=AnalysisStore)
        mock_store.load_cached_worker_result.return_value = None

        pipeline = LintPipeline(store=mock_store)
        result = pipeline.analyze_paths([src_file], jobs=1)

        assert mock_store.load_cached_worker_result.called
        assert mock_store.store_cached_worker_result.called
        assert mock_store.record_run.called
        assert result.cache_stats == {"hits": 0, "misses": 1}
