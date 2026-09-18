from __future__ import annotations

from dataclasses import asdict

import pytest

from src.pkg.engine import WorkerResult, _worker_result_from_payload
from src.pkg.semantic.models import InstanceRecord, ParameterOverride, PortConnection
from src.pkg.semantic.symbol_table import SymbolTable


class TestPortConnection:
    def test_construction_and_typed_attributes(self) -> None:
        conn = PortConnection(
            kind="named",
            location={"line": 10, "col": 5, "file": "top.sv"},
            port_name="clk",
            expr_text="sys_clk",
            expr_name="sys_clk",
            expr_width=1,
            expr_signed=False,
        )
        assert conn.kind == "named"
        assert conn.location == {"line": 10, "col": 5, "file": "top.sv"}
        assert conn.port_name == "clk"
        assert conn.expr_text == "sys_clk"
        assert conn.expr_name == "sys_clk"
        assert conn.expr_width == 1
        assert conn.expr_signed is False

    def test_default_values(self) -> None:
        conn = PortConnection(kind="empty")
        assert conn.kind == "empty"
        assert conn.location == {"line": 0, "col": 0}
        assert conn.port_name is None
        assert conn.expr_text is None
        assert conn.expr_name is None
        assert conn.expr_width is None
        assert conn.expr_signed is None

    def test_mapping_interface(self) -> None:
        conn = PortConnection(
            kind="named",
            port_name="data_in",
            expr_text="data[7:0]",
            expr_width=8,
        )
        assert conn["kind"] == "named"
        assert conn["port_name"] == "data_in"
        assert conn.get("port_name") == "data_in"
        assert conn.get("missing", "default_val") == "default_val"
        assert "port_name" in conn
        assert "nonexistent" not in conn
        assert len(conn) == 7

        with pytest.raises(KeyError):
            _ = conn["nonexistent"]

        d = dict(conn)
        assert d["port_name"] == "data_in"
        assert d["expr_width"] == 8

    def test_to_dict_and_from_dict_roundtrip(self) -> None:
        original = PortConnection(
            kind="named",
            location={"line": 15, "col": 2, "file": "test.sv"},
            port_name="rst_n",
            expr_text="reset_n",
            expr_name="reset_n",
            expr_width=1,
            expr_signed=False,
        )
        d = original.to_dict()
        assert isinstance(d, dict)
        assert d["port_name"] == "rst_n"

        reconstructed = PortConnection.from_dict(d)
        assert reconstructed == original
        # Idempotence when passing PortConnection to from_dict
        assert PortConnection.from_dict(reconstructed) is reconstructed


class TestParameterOverride:
    def test_construction_and_mapping(self) -> None:
        override = ParameterOverride(
            kind="named",
            location={"line": 8, "col": 3},
            param_name="WIDTH",
            expr_text="8",
            expr_value=8,
        )
        assert override.kind == "named"
        assert override.param_name == "WIDTH"
        assert override.expr_text == "8"
        assert override.expr_value == 8
        assert override["param_name"] == "WIDTH"
        assert override["expr_text"] == "8"
        assert override["expr_value"] == 8
        assert override.get("param_name") == "WIDTH"
        assert "param_name" in override
        assert len(override) == 5

        d = override.to_dict()
        assert d == {
            "kind": "named",
            "location": {"line": 8, "col": 3},
            "param_name": "WIDTH",
            "expr_text": "8",
            "expr_value": 8,
        }

        reconstructed = ParameterOverride.from_dict(d)
        assert reconstructed == override
        assert ParameterOverride.from_dict(reconstructed) is reconstructed


class TestInstanceRecord:
    def test_construction_and_typed_attributes(self) -> None:
        conn = PortConnection(kind="named", port_name="a", expr_text="x")
        param = ParameterOverride(kind="named", param_name="P")
        inst = InstanceRecord(
            parent_module="top",
            child_module="sub",
            instance_name="u_sub",
            location={"line": 20, "col": 4, "file": "top.sv"},
            connection_style="named",
            connections=[conn],
            parameter_override_style="named",
            parameter_overrides=[param],
            generate_branch_signature=((("gen_block", 1, 1), 0),),
        )
        assert inst.parent_module == "top"
        assert inst.child_module == "sub"
        assert inst.instance_name == "u_sub"
        assert inst.connection_style == "named"
        assert inst.connections[0].port_name == "a"
        assert inst.parameter_overrides[0].param_name == "P"
        assert inst.generate_branch_signature == ((("gen_block", 1, 1), 0),)

    def test_mapping_interface(self) -> None:
        inst = InstanceRecord(
            parent_module="top",
            child_module="child",
            instance_name="u_child",
            connection_style="empty",
        )
        assert inst["parent_module"] == "top"
        assert inst["child_module"] == "child"
        assert inst["instance_name"] == "u_child"
        assert inst.get("connection_style") == "empty"
        assert inst.get("nonexistent", 42) == 42
        assert "instance_name" in inst
        assert "not_a_field" not in inst
        assert len(inst) == 9

        with pytest.raises(KeyError):
            _ = inst["unknown_key"]

    def test_to_dict_and_from_dict_roundtrip(self) -> None:
        conn = PortConnection(kind="named", port_name="clk", expr_text="clk")
        param = ParameterOverride(kind="named", param_name="DATA_W")
        original = InstanceRecord(
            parent_module="mod_a",
            child_module="mod_b",
            instance_name="u_b",
            location={"line": 40, "col": 8, "file": "mod.sv"},
            connection_style="named",
            connections=[conn],
            parameter_override_style="named",
            parameter_overrides=[param],
            generate_branch_signature=((("gen_item", 10, 2), 1),),
        )
        d = original.to_dict()
        assert isinstance(d, dict)
        assert isinstance(d["connections"][0], dict)
        assert isinstance(d["parameter_overrides"][0], dict)

        reconstructed = InstanceRecord.from_dict(d)
        assert reconstructed.parent_module == original.parent_module
        assert reconstructed.instance_name == original.instance_name
        assert len(reconstructed.connections) == 1
        assert isinstance(reconstructed.connections[0], PortConnection)
        assert reconstructed.connections[0].port_name == "clk"
        assert len(reconstructed.parameter_overrides) == 1
        assert isinstance(reconstructed.parameter_overrides[0], ParameterOverride)
        assert reconstructed.parameter_overrides[0].param_name == "DATA_W"
        assert reconstructed.generate_branch_signature == ((("gen_item", 10, 2), 1),)

    def test_from_dict_with_nested_lists_in_signature(self) -> None:
        # JSON deserialization turns tuples into lists of lists
        raw_dict = {
            "parent_module": "top",
            "child_module": "leaf",
            "instance_name": "u_leaf",
            "location": {"line": 1, "col": 1},
            "connection_style": "wildcard",
            "connections": [{"kind": "wildcard", "location": {"line": 1, "col": 1}}],
            "parameter_override_style": "none",
            "parameter_overrides": [],
            "generate_branch_signature": [[["case_arm", 5, 2], 0]],
        }
        inst = InstanceRecord.from_dict(raw_dict)
        assert isinstance(inst.connections[0], PortConnection)
        assert inst.connections[0].kind == "wildcard"
        assert inst.generate_branch_signature == ((("case_arm", 5, 2), 0),)


class TestSymbolTableAndWorkerResultIntegration:
    def test_symbol_table_register_instance_record(self) -> None:
        st = SymbolTable()
        inst = InstanceRecord(
            parent_module="parent",
            child_module="child",
            instance_name="u_child",
        )
        st.register_instantiation(inst)
        assert len(st.instantiations) == 1
        assert st.instantiations[0] is inst

    def test_symbol_table_register_raw_dict_auto_normalizes(self) -> None:
        st = SymbolTable()
        raw = {
            "parent_module": "top",
            "child_module": "sub",
            "instance_name": "u_sub",
            "connection_style": "empty",
            "connections": [],
        }
        st.register_instantiation(raw)
        assert len(st.instantiations) == 1
        assert isinstance(st.instantiations[0], InstanceRecord)
        assert st.instantiations[0].instance_name == "u_sub"

    def test_worker_result_asdict_and_deserialization(self) -> None:
        inst = InstanceRecord(
            parent_module="top",
            child_module="sub",
            instance_name="u_sub",
            connection_style="named",
            connections=[PortConnection(kind="named", port_name="clk", expr_text="clk")],
        )
        wr = WorkerResult(
            diagnostics=[],
            modules=[],
            primitives=[],
            module_references=[],
            instantiation_edges=[],
            instantiations=[inst],
        )

        serialized = asdict(wr)
        assert isinstance(serialized["instantiations"], list)
        assert isinstance(serialized["instantiations"][0], dict)
        assert serialized["instantiations"][0]["instance_name"] == "u_sub"

        reconstructed_wr = _worker_result_from_payload(serialized)
        assert len(reconstructed_wr.instantiations) == 1
        reconstructed_inst = reconstructed_wr.instantiations[0]
        assert isinstance(reconstructed_inst, InstanceRecord)
        assert reconstructed_inst.instance_name == "u_sub"
        assert isinstance(reconstructed_inst.connections[0], PortConnection)
        assert reconstructed_inst.connections[0].port_name == "clk"
