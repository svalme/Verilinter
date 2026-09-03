from pathlib import Path

from src.run_lint import run


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
PORT_CONNECTION_ISSUES_DATA = DATA_DIR / "port_connection_issues.sv"
PORT_CONNECTION_ADVANCED_DATA = DATA_DIR / "port_connection_advanced.sv"
WILDCARD_PORT_CONNECTION_DATA = DATA_DIR / "wildcard_port_connection.sv"
UNDEFINED_MODULE_PARAM_OVERRIDE_DATA = DATA_DIR / "undefined_module_param_override.sv"


class TestModuleConnectionRules:
    def test_reports_basic_connection_issues(self) -> None:
        diagnostics = run([PORT_CONNECTION_ISSUES_DATA], jobs=1)

        assert any(d["code"] == "NO_UNCONNECTED_INSTANCE_PORTS" for d in diagnostics)
        assert any(d["code"] == "NO_DUPLICATE_NAMED_PORT_CONNECTION" for d in diagnostics)
        assert any(d["code"] == "NO_MIXED_PORT_CONNECTION_STYLE" for d in diagnostics)
        assert any(d["code"] == "PORT_CONNECTION_WIDTH_MISMATCH" for d in diagnostics)
        assert any(d["code"] == "PORT_CONNECTION_SIGNEDNESS_MISMATCH" for d in diagnostics)

    def test_reports_advanced_connection_and_override_issues(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        assert any(d["code"] == "UNKNOWN_NAMED_PORT_CONNECTION" for d in diagnostics)
        assert any(d["code"] == "PORT_CONNECTION_WIDTH_UNKNOWN" for d in diagnostics)
        assert any(d["code"] == "UNREAD_INSTANCE_OUTPUT" for d in diagnostics)
        assert any(d["code"] == "EXTRA_ORDERED_PORT_CONNECTION" for d in diagnostics)
        assert any(d["code"] == "UNKNOWN_NAMED_PARAMETER_OVERRIDE" for d in diagnostics)
        assert any(d["code"] == "NO_DUPLICATE_NAMED_PARAMETER_OVERRIDE" for d in diagnostics)
        assert any(d["code"] == "NO_MIXED_PARAMETER_OVERRIDE_STYLE" for d in diagnostics)
        assert any(d["code"] == "NO_ORDERED_PORT_CONNECTIONS" for d in diagnostics)
        assert any(d["code"] == "NO_ORDERED_PARAMETER_OVERRIDES" for d in diagnostics)

    def test_wildcard_connections_do_not_trigger_explicit_mapping_checks(self) -> None:
        diagnostics = run([WILDCARD_PORT_CONNECTION_DATA], jobs=1)

        assert any(d["code"] == "NO_WILDCARD_PORT_CONNECTION" for d in diagnostics)
        blocked_codes = {
            "NO_UNCONNECTED_INSTANCE_PORTS",
            "PORT_CONNECTION_WIDTH_MISMATCH",
            "PORT_CONNECTION_WIDTH_UNKNOWN",
            "PORT_CONNECTION_SIGNEDNESS_MISMATCH",
            "UNREAD_INSTANCE_OUTPUT",
        }
        assert not any(d["code"] in blocked_codes for d in diagnostics)

    def test_undefined_module_does_not_pile_on_unknown_connection_details(self) -> None:
        diagnostics = run([UNDEFINED_MODULE_PARAM_OVERRIDE_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("UNDEFINED_MODULE") == 1
        assert "UNKNOWN_NAMED_PARAMETER_OVERRIDE" not in codes
        assert "UNKNOWN_NAMED_PORT_CONNECTION" not in codes
