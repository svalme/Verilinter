"""`run` reports the net, primitive, assertion, system task and data type rules."""
from pathlib import Path
from src.run_lint import run


DEFPARAM_USAGE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "defparam_usage.v"


FORCE_RELEASE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "force_release.v"


ASSIGN_DEASSIGN_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "assign_deassign.v"


WAND_WOR_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "wand_wor.v"


TRIREG_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "trireg.v"


SUPPLY0_SUPPLY1_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "supply0_supply1.v"


TRAN_RTRAN_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "tran_rtran.v"


TRANIF_RTRANIF_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "tranif_rtranif.v"


SPECIFY_BLOCK_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "specify_block.v"


PRIMITIVE_DECLARATION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "primitive_declaration.v"


GATE_PRIMITIVE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "gate_primitive.v"


ALIAS_STATEMENT_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "alias_statement.sv"


BIND_DIRECTIVE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "bind_directive.sv"


DELAY_CONTROL_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "delay_control.v"


IMMEDIATE_ASSERTION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "immediate_assertion.sv"


CONCURRENT_ASSERTION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "concurrent_assertion.sv"


DISPLAY_SYSTEM_TASK_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "display_system_task.v"


SIMULATION_CONTROL_TASK_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "simulation_control_task.v"


CLASS_DECLARATION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "class_declaration.sv"


COVERGROUP_DECLARATION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "covergroup_declaration.sv"


SEQUENCE_DECLARATION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "sequence_declaration.sv"


PROPERTY_DECLARATION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "property_declaration.sv"


FUNCTION_DECLARATION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "function_declaration.sv"


UWIRE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "uwire.v"


LET_DECLARATION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "let_declaration.sv"


CONFIG_DECLARATION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "config_declaration.v"


RANDSEQUENCE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "randsequence.sv"


EXPECT_RESTRICT_PROPERTY_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "expect_restrict_property.sv"


VIRTUAL_INTERFACE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "virtual_interface.sv"


DPI_IMPORT_EXPORT_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "dpi_import_export.sv"


REAL_TYPE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "real_type.v"


STRING_TYPE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "string_type.sv"


CHANDLE_TYPE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "chandle_type.sv"


RANDOM_SYSTEM_FUNCTION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "random_system_function.v"


TIME_SYSTEM_FUNCTION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "time_system_function.v"


VCD_DUMP_TASK_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "vcd_dump_task.v"


FILE_IO_SYSTEM_TASK_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "file_io_system_task.v"


PLUSARGS_SYSTEM_FUNCTION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "plusargs_system_function.v"


ASSERTION_CONTROL_TASK_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "assertion_control_task.sv"


QUEUE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "queue.sv"


DYNAMIC_ARRAY_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "dynamic_array.sv"


ASSOCIATIVE_ARRAY_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "associative_array.sv"


UNIQUE0_IF_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "unique0_if.v"


SWITCH_PRIMITIVE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "switch_primitive.v"


class TestRunReportsNetPrimitiveAndTypeRules:
    def test_run_reports_defparam_rule(self) -> None:
        diagnostics = run([DEFPARAM_USAGE_DATA], jobs=1)

        assert any(d["code"] == "NO_DEFPARAM" for d in diagnostics)
        assert any("defparam" in d["message"] for d in diagnostics)
        assert not any(d["code"] == "NO_IMPLICIT_NET" for d in diagnostics)

    def test_run_reports_force_release_rule(self) -> None:
        diagnostics = run([FORCE_RELEASE_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_FORCE_RELEASE") == 2
        assert any("force/release" in d["message"] for d in diagnostics)

    def test_run_reports_assign_deassign_rule(self) -> None:
        diagnostics = run([ASSIGN_DEASSIGN_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_ASSIGN_DEASSIGN") == 2
        assert any("assign/deassign" in d["message"] for d in diagnostics)

    def test_run_reports_wand_wor_rule(self) -> None:
        diagnostics = run([WAND_WOR_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_WAND_WOR") == 2
        assert any("wand/wor" in d["message"] for d in diagnostics)

    def test_run_reports_trireg_rule(self) -> None:
        diagnostics = run([TRIREG_DATA], jobs=1)

        assert any(d["code"] == "NO_TRIREG" for d in diagnostics)
        assert any("trireg" in d["message"] for d in diagnostics)

    def test_run_reports_supply0_supply1_rule(self) -> None:
        diagnostics = run([SUPPLY0_SUPPLY1_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_SUPPLY0_SUPPLY1") == 2
        assert any("supply0/supply1" in d["message"] for d in diagnostics)

    def test_run_reports_tran_rtran_rule(self) -> None:
        diagnostics = run([TRAN_RTRAN_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_TRAN_RTRAN") == 2
        assert any("tran/rtran" in d["message"] for d in diagnostics)

    def test_run_reports_tranif_rtranif_rule(self) -> None:
        diagnostics = run([TRANIF_RTRANIF_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_TRANIF_RTRANIF") == 4
        assert any("tranif/rtranif" in d["message"] for d in diagnostics)

    def test_run_reports_specify_block_rule(self) -> None:
        diagnostics = run([SPECIFY_BLOCK_DATA], jobs=1)

        assert any(d["code"] == "NO_SPECIFY_BLOCK" for d in diagnostics)
        assert any("specify block" in d["message"] for d in diagnostics)

    def test_run_reports_primitive_declaration_rule(self) -> None:
        diagnostics = run([PRIMITIVE_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_PRIMITIVE_DECLARATION" for d in diagnostics)
        assert any("primitive" in d["message"] for d in diagnostics)

    def test_run_reports_gate_primitive_rule(self) -> None:
        diagnostics = run([GATE_PRIMITIVE_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_GATE_PRIMITIVE") == 2
        assert any("gate-level primitives" in d["message"] for d in diagnostics)

    def test_run_reports_alias_statement_rule(self) -> None:
        diagnostics = run([ALIAS_STATEMENT_DATA], jobs=1)

        assert any(d["code"] == "NO_ALIAS_STATEMENT" for d in diagnostics)
        assert any("alias statement" in d["message"] for d in diagnostics)

    def test_run_reports_bind_directive_rule(self) -> None:
        diagnostics = run([BIND_DIRECTIVE_DATA], jobs=1)

        assert any(d["code"] == "NO_BIND_DIRECTIVE" for d in diagnostics)
        assert any("bind directive" in d["message"] for d in diagnostics)
        assert not any(d["code"] == "NO_IMPLICIT_NET" for d in diagnostics)

    def test_run_reports_delay_control_rule(self) -> None:
        diagnostics = run([DELAY_CONTROL_DATA], jobs=1)

        assert any(d["code"] == "NO_DELAY_CONTROL" for d in diagnostics)
        assert any("delay control" in d["message"] for d in diagnostics)

    def test_run_reports_immediate_assertion_rule(self) -> None:
        diagnostics = run([IMMEDIATE_ASSERTION_DATA], jobs=1)

        assert any(d["code"] == "NO_IMMEDIATE_ASSERTION" for d in diagnostics)
        assert any("immediate assertions" in d["message"] for d in diagnostics)

    def test_run_reports_concurrent_assertion_rule(self) -> None:
        diagnostics = run([CONCURRENT_ASSERTION_DATA], jobs=1)

        assert any(d["code"] == "NO_CONCURRENT_ASSERTION" for d in diagnostics)
        assert any("concurrent assertions" in d["message"] for d in diagnostics)

    def test_run_reports_display_system_task_rule(self) -> None:
        diagnostics = run([DISPLAY_SYSTEM_TASK_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_DISPLAY_SYSTEM_TASK") == 2
        assert any("$display" in d["message"] for d in diagnostics)

    def test_run_reports_simulation_control_task_rule(self) -> None:
        diagnostics = run([SIMULATION_CONTROL_TASK_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_SIMULATION_CONTROL_TASK") == 2
        assert any("$stop" in d["message"] for d in diagnostics)

    def test_run_reports_class_declaration_rule(self) -> None:
        diagnostics = run([CLASS_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_CLASS_DECLARATION" for d in diagnostics)
        assert any("class declarations" in d["message"] for d in diagnostics)

    def test_run_reports_covergroup_declaration_rule(self) -> None:
        diagnostics = run([COVERGROUP_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_COVERGROUP_DECLARATION" for d in diagnostics)
        assert any("covergroup declarations" in d["message"] for d in diagnostics)

    def test_run_reports_sequence_declaration_rule(self) -> None:
        diagnostics = run([SEQUENCE_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_SEQUENCE_DECLARATION" for d in diagnostics)
        assert any("sequence declarations" in d["message"] for d in diagnostics)

    def test_run_reports_property_declaration_rule(self) -> None:
        diagnostics = run([PROPERTY_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_PROPERTY_DECLARATION" for d in diagnostics)
        assert any("property declarations" in d["message"] for d in diagnostics)

    def test_run_reports_function_declaration_rule(self) -> None:
        diagnostics = run([FUNCTION_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_FUNCTION_DECLARATION" for d in diagnostics)
        assert any("function declarations" in d["message"] for d in diagnostics)
        assert not any(
            d["code"] == "NO_IMPLICIT_NET" and "do_work" in d["message"] for d in diagnostics
        )

    def test_run_reports_uwire_rule(self) -> None:
        diagnostics = run([UWIRE_DATA], jobs=1)

        assert any(d["code"] == "NO_UWIRE" for d in diagnostics)
        assert any("uwire" in d["message"] for d in diagnostics)

    def test_run_reports_let_declaration_rule(self) -> None:
        diagnostics = run([LET_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_LET_DECLARATION" for d in diagnostics)
        assert any("let declarations" in d["message"] for d in diagnostics)

    def test_run_reports_config_declaration_rule(self) -> None:
        diagnostics = run([CONFIG_DECLARATION_DATA], jobs=1)

        assert any(d["code"] == "NO_CONFIG_DECLARATION" for d in diagnostics)
        assert any("config declarations" in d["message"] for d in diagnostics)

    def test_run_reports_randsequence_rule(self) -> None:
        diagnostics = run([RANDSEQUENCE_DATA], jobs=1)

        assert any(d["code"] == "NO_RANDSEQUENCE" for d in diagnostics)
        assert any("randsequence" in d["message"] for d in diagnostics)

    def test_run_reports_expect_restrict_property_rule(self) -> None:
        diagnostics = run([EXPECT_RESTRICT_PROPERTY_DATA], jobs=1)

        assert any(d["code"] == "NO_EXPECT_RESTRICT_PROPERTY" for d in diagnostics)
        assert any("expect/restrict property" in d["message"] for d in diagnostics)

    def test_run_reports_virtual_interface_rule(self) -> None:
        diagnostics = run([VIRTUAL_INTERFACE_DATA], jobs=1)

        assert any(d["code"] == "NO_VIRTUAL_INTERFACE" for d in diagnostics)
        assert any("virtual interface" in d["message"] for d in diagnostics)

    def test_run_reports_dpi_import_export_rule(self) -> None:
        diagnostics = run([DPI_IMPORT_EXPORT_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_DPI_IMPORT_EXPORT") == 2
        assert any("DPI import/export" in d["message"] for d in diagnostics)

    def test_run_reports_real_type_rule(self) -> None:
        diagnostics = run([REAL_TYPE_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_REAL_TYPE") == 3
        assert any("real/shortreal/realtime" in d["message"] for d in diagnostics)

    def test_run_reports_string_type_rule(self) -> None:
        diagnostics = run([STRING_TYPE_DATA], jobs=1)

        assert any(d["code"] == "NO_STRING_TYPE" for d in diagnostics)
        assert any("string type" in d["message"] for d in diagnostics)

    def test_run_reports_chandle_type_rule(self) -> None:
        diagnostics = run([CHANDLE_TYPE_DATA], jobs=1)

        assert any(d["code"] == "NO_CHANDLE_TYPE" for d in diagnostics)
        assert any("chandle type" in d["message"] for d in diagnostics)

    def test_run_reports_random_system_function_rule(self) -> None:
        diagnostics = run([RANDOM_SYSTEM_FUNCTION_DATA], jobs=1)

        assert any(d["code"] == "NO_RANDOM_SYSTEM_FUNCTION" for d in diagnostics)
        assert any("$random" in d["message"] for d in diagnostics)

    def test_run_reports_time_system_function_rule(self) -> None:
        diagnostics = run([TIME_SYSTEM_FUNCTION_DATA], jobs=1)

        assert any(d["code"] == "NO_TIME_SYSTEM_FUNCTION" for d in diagnostics)
        assert any("$time" in d["message"] for d in diagnostics)

    def test_run_reports_vcd_dump_task_rule(self) -> None:
        diagnostics = run([VCD_DUMP_TASK_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_VCD_DUMP_TASK") == 2
        assert any("VCD dump" in d["message"] for d in diagnostics)

    def test_run_reports_file_io_system_task_rule(self) -> None:
        diagnostics = run([FILE_IO_SYSTEM_TASK_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_FILE_IO_SYSTEM_TASK") == 3
        assert any("file I/O" in d["message"] for d in diagnostics)

    def test_run_reports_plusargs_system_function_rule(self) -> None:
        diagnostics = run([PLUSARGS_SYSTEM_FUNCTION_DATA], jobs=1)

        assert any(d["code"] == "NO_PLUSARGS_SYSTEM_FUNCTION" for d in diagnostics)
        assert any("plusargs" in d["message"] for d in diagnostics)

    def test_run_reports_assertion_control_task_rule(self) -> None:
        diagnostics = run([ASSERTION_CONTROL_TASK_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_ASSERTION_CONTROL_TASK") == 2
        assert any("assertion-control" in d["message"] for d in diagnostics)

    def test_run_reports_queue_rule(self) -> None:
        diagnostics = run([QUEUE_DATA], jobs=1)

        assert any(d["code"] == "NO_QUEUE" for d in diagnostics)
        assert any("queue" in d["message"].lower() for d in diagnostics)

    def test_run_reports_dynamic_array_rule(self) -> None:
        diagnostics = run([DYNAMIC_ARRAY_DATA], jobs=1)

        assert any(d["code"] == "NO_DYNAMIC_ARRAY" for d in diagnostics)
        assert any("dynamic array" in d["message"] for d in diagnostics)

    def test_run_reports_associative_array_rule(self) -> None:
        diagnostics = run([ASSOCIATIVE_ARRAY_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("NO_ASSOCIATIVE_ARRAY") == 2
        assert any("associative array" in d["message"] for d in diagnostics)

    def test_run_reports_unique0_if_rule(self) -> None:
        diagnostics = run([UNIQUE0_IF_DATA], jobs=1)

        assert any(d["code"] == "NO_UNIQUE0_IF" for d in diagnostics)
        assert any("unique0 if" in d["message"] for d in diagnostics)

    def test_run_reports_switch_primitive_rule(self) -> None:
        diagnostics = run([SWITCH_PRIMITIVE_DATA], jobs=1)

        assert any(d["code"] == "NO_SWITCH_PRIMITIVE" for d in diagnostics)
        assert any("switch-level primitives" in d["message"] for d in diagnostics)
