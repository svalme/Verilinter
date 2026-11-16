"""`run` reports the instance, port connection and parameter override rules."""
from pathlib import Path
from src.run_lint import run


PORT_CONNECTION_ISSUES_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "port_connection_issues.sv"


PORT_CONNECTION_ADVANCED_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "port_connection_advanced.sv"


WILDCARD_PORT_CONNECTION_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "wildcard_port_connection.sv"


UNDEFINED_MODULE_PARAM_OVERRIDE_DATA = Path(__file__).resolve().parent.parents[1] / "data" / "undefined_module_param_override.sv"


class TestRunReportsInstanceRules:
    def test_run_reports_unconnected_instance_ports_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ISSUES_DATA], jobs=1)

        assert any(d["code"] == "NO_UNCONNECTED_INSTANCE_PORTS" for d in diagnostics)
        assert any("u_unconn" in d["message"] and "y" in d["message"] for d in diagnostics)

    def test_run_reports_duplicate_named_port_connection_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ISSUES_DATA], jobs=1)

        assert any(d["code"] == "NO_DUPLICATE_NAMED_PORT_CONNECTION" for d in diagnostics)
        assert any("u_dup" in d["message"] and "data" in d["message"] for d in diagnostics)

    def test_run_reports_mixed_port_connection_style_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ISSUES_DATA], jobs=1)

        assert any(d["code"] == "NO_MIXED_PORT_CONNECTION_STYLE" for d in diagnostics)
        assert any("u_mixed" in d["message"] for d in diagnostics)

    def test_run_reports_port_connection_width_mismatch_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ISSUES_DATA], jobs=1)

        assert any(d["code"] == "PORT_CONNECTION_WIDTH_MISMATCH" for d in diagnostics)
        assert any("u_width" in d["message"] and "width 8" in d["message"] for d in diagnostics)

    def test_run_reports_port_connection_signedness_mismatch_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ISSUES_DATA], jobs=1)

        assert any(d["code"] == "PORT_CONNECTION_SIGNEDNESS_MISMATCH" for d in diagnostics)
        assert any("u_width" in d["message"] and "unsigned" in d["message"] for d in diagnostics)

    def test_run_reports_slice_and_replication_width_mismatches(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        mismatches = [d for d in diagnostics if d["code"] == "PORT_CONNECTION_WIDTH_MISMATCH"]
        assert any("u_slice_mismatch" in d["message"] and "bus8[5:0]" in d["message"] for d in mismatches)
        assert any("u_rep_mismatch" in d["message"] and "{3{pair}}" in d["message"] for d in mismatches)

    def test_run_reports_unknown_named_port_connection_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        assert any(d["code"] == "UNKNOWN_NAMED_PORT_CONNECTION" for d in diagnostics)
        assert any("u_bad_port" in d["message"] and "qq" in d["message"] for d in diagnostics)

    def test_run_reports_width_unknown_when_inference_is_not_confident(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        assert any(d["code"] == "PORT_CONNECTION_WIDTH_UNKNOWN" for d in diagnostics)
        assert any("u_rep_mismatch" in d["message"] and "Cannot infer width confidently" in d["message"] for d in diagnostics)
        assert any("u_unknown" in d["message"] and "unknown port width" in d["message"] for d in diagnostics)

    def test_run_reports_unread_instance_output_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        assert any(d["code"] == "UNREAD_INSTANCE_OUTPUT" for d in diagnostics)
        assert any("u_slice_mismatch" in d["message"] and "out_unused" in d["message"] for d in diagnostics)

    def test_run_reports_extra_ordered_port_connection_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        assert any(d["code"] == "EXTRA_ORDERED_PORT_CONNECTION" for d in diagnostics)

    def test_run_reports_unknown_named_parameter_override_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        assert any(
            d["code"] == "UNKNOWN_NAMED_PARAMETER_OVERRIDE" and "BOGUS_PARAM" in d["message"]
            for d in diagnostics
        )

    def test_run_reports_duplicate_named_parameter_override_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        assert any(d["code"] == "NO_DUPLICATE_NAMED_PARAMETER_OVERRIDE" for d in diagnostics)

    def test_run_reports_mixed_parameter_override_style_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        assert any(d["code"] == "NO_MIXED_PARAMETER_OVERRIDE_STYLE" for d in diagnostics)

    def test_run_reports_ordered_port_connections_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        assert any(d["code"] == "NO_ORDERED_PORT_CONNECTIONS" for d in diagnostics)
        assert any("u_extra_ordered" in d["message"] for d in diagnostics)

    def test_run_reports_ordered_parameter_overrides_rule(self) -> None:
        diagnostics = run([PORT_CONNECTION_ADVANCED_DATA], jobs=1)

        assert any(d["code"] == "NO_ORDERED_PARAMETER_OVERRIDES" for d in diagnostics)
        assert any("u_mixed_param_override" in d["message"] for d in diagnostics)

    def test_run_reports_wildcard_port_connection_rule(self) -> None:
        diagnostics = run([WILDCARD_PORT_CONNECTION_DATA], jobs=1)

        assert any(d["code"] == "NO_WILDCARD_PORT_CONNECTION" for d in diagnostics)
        assert any("u_wild" in d["message"] and "(.*)" in d["message"] for d in diagnostics)

    def test_run_does_not_pile_on_explicit_port_mapping_checks_for_wildcard_connections(self) -> None:
        diagnostics = run([WILDCARD_PORT_CONNECTION_DATA], jobs=1)

        blocked_codes = {
            "NO_UNCONNECTED_INSTANCE_PORTS",
            "PORT_CONNECTION_WIDTH_MISMATCH",
            "PORT_CONNECTION_WIDTH_UNKNOWN",
            "PORT_CONNECTION_SIGNEDNESS_MISMATCH",
            "UNREAD_INSTANCE_OUTPUT",
        }
        assert not any(d["code"] in blocked_codes for d in diagnostics)

    def test_run_does_not_double_report_unknown_parameter_override_for_undefined_module(self) -> None:
        """Regression test: when the instantiated module type is undefined, that's
        already `UNDEFINED_MODULE`'s concern -- `UNKNOWN_NAMED_PARAMETER_OVERRIDE`
        (and the equivalent port-connection check) must not pile on a misleading
        'unknown parameter/port' diagnostic per connection on top of it, since there
        is no real parameter/port list to check against in the first place."""
        diagnostics = run([UNDEFINED_MODULE_PARAM_OVERRIDE_DATA], jobs=1)

        codes = [d["code"] for d in diagnostics]
        assert codes.count("UNDEFINED_MODULE") == 1
        assert "UNKNOWN_NAMED_PARAMETER_OVERRIDE" not in codes
        assert "UNKNOWN_NAMED_PORT_CONNECTION" not in codes
