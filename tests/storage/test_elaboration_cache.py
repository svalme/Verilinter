"""The elaborated width record is stored per file set and reused only while every input is unchanged."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from src.pkg.analysis_store import AnalysisStore
from src.pkg.engine import analyze
from src.pkg.parser.elaborated_widths import ElaboratedWidths

HEADER = "`define PORT_WIDTH 8\n"

CHILD = """
module child (input logic [`PORT_WIDTH-1:0] a);
endmodule
"""

TOP = """
`include "defs.svh"
module top(input logic [7:0] x);
  child u_c(.a(x));
endmodule
"""


class Project:
    """A small file set in `tmp_path`, analyzed against one store, counting how often the record is built."""

    def __init__(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self.root = tmp_path
        self.include_dir = tmp_path / "inc"
        self.include_dir.mkdir()
        self.store_path = tmp_path / "store.sqlite"
        self.builds = 0
        self.write("inc/defs.svh", HEADER)
        # `include` in the child needs the header too, so the child includes it explicitly.
        self.write("child.sv", '`include "defs.svh"\n' + CHILD)
        self.write("top.sv", TOP)
        original = ElaboratedWidths.build.__func__
        project = self

        def counting(cls, *args, **kwargs):
            project.builds += 1
            return original(cls, *args, **kwargs)

        monkeypatch.setattr(ElaboratedWidths, "build", classmethod(counting))

    def write(self, name: str, text: str) -> Path:
        path = self.root / name
        path.write_bytes(text.encode("utf-8"))
        return path

    def run(self, names: tuple[str, ...] = ("child.sv", "top.sv"), **overrides):
        options = {"include_dirs": [str(self.include_dir)], "store_path": self.store_path, "elaborated_widths": True}
        options.update(overrides)
        return analyze([self.root / name for name in names], rule_profile="rtl_strict", **options)

    def rows(self) -> list[tuple[str, str]]:
        connection = sqlite3.connect(self.store_path)
        try:
            return list(connection.execute("SELECT set_id, input_key FROM cached_elaboration"))
        finally:
            connection.close()


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Project:
    return Project(tmp_path, monkeypatch)


def _codes(result) -> list[str]:
    return sorted(d["code"] for d in result.diagnostics)


def test_a_second_run_reads_the_record_and_reports_the_same_findings(project: Project) -> None:
    first = project.run()
    second = project.run()

    assert project.builds == 1
    assert _codes(first) == _codes(second)
    assert first.diagnostics == second.diagnostics


def test_a_run_without_the_record_leaves_the_store_without_one(project: Project) -> None:
    project.run(elaborated_widths=False)

    assert project.builds == 0
    assert project.rows() == []


def test_an_edited_file_builds_the_record_again(project: Project) -> None:
    project.run()
    project.write("top.sv", TOP.replace("[7:0] x", "[3:0] x"))
    project.run()

    assert project.builds == 2


def test_an_edited_header_builds_the_record_again(project: Project) -> None:
    project.run()
    project.write("inc/defs.svh", "`define PORT_WIDTH 4\n")
    project.run()

    assert project.builds == 2


def test_other_defines_build_the_record_again(project: Project) -> None:
    project.run(defines=["A=1"])
    project.run(defines=["A=2"])

    assert project.builds == 2


def test_other_include_directories_build_the_record_again(project: Project) -> None:
    extra = project.root / "extra"
    extra.mkdir()
    project.run(include_dirs=[str(project.include_dir)])
    project.run(include_dirs=[str(project.include_dir), str(extra)])

    assert project.builds == 2


def test_a_different_file_set_builds_the_record_again(project: Project) -> None:
    project.write("extra.sv", "module extra; endmodule\n")
    project.run()
    project.run(names=("child.sv", "top.sv", "extra.sv"))

    assert project.builds == 2


def test_repeated_edits_keep_one_row_for_the_file_set(project: Project) -> None:
    for width in (3, 4, 5):
        project.write("top.sv", TOP.replace("[7:0] x", f"[{width}:0] x"))
        project.run()

    assert project.builds == 3
    assert len(project.rows()) == 1


def test_a_run_without_the_cache_builds_the_record_and_stores_it(project: Project) -> None:
    project.run(use_cache=False)
    project.run(use_cache=False)
    assert project.builds == 2

    project.run()
    assert project.builds == 2


def test_an_unreadable_record_is_built_again(project: Project) -> None:
    project.run()
    connection = sqlite3.connect(project.store_path)
    try:
        with connection:
            connection.execute("UPDATE cached_elaboration SET record_json = 'not json'")
    finally:
        connection.close()
    project.run()

    assert project.builds == 2
    project.run()
    assert project.builds == 2


def test_a_record_of_another_layout_is_built_again(project: Project) -> None:
    project.run()
    connection = sqlite3.connect(project.store_path)
    try:
        with connection:
            (record_json,) = connection.execute("SELECT record_json FROM cached_elaboration").fetchone()
            payload = json.loads(record_json)
            payload["layout"] = payload["layout"] + 1
            connection.execute("UPDATE cached_elaboration SET record_json = ?", (json.dumps(payload),))
    finally:
        connection.close()
    project.run()

    assert project.builds == 2


def test_pruning_removes_old_records(project: Project) -> None:
    project.run()
    connection = sqlite3.connect(project.store_path)
    try:
        with connection:
            connection.execute("UPDATE cached_elaboration SET cached_at = '2000-01-01T00:00:00+00:00'")
    finally:
        connection.close()

    AnalysisStore(project.store_path).prune_cache(older_than_days=1)

    assert project.rows() == []


def test_the_stored_record_answers_as_the_built_one_does(tmp_path: Path) -> None:
    path = tmp_path / "top.sv"
    path.write_bytes(
        b"module child(input logic [3:0] a, output logic y); endmodule\n"
        b"module top(input logic [3:0] x, output logic z);\n"
        b"  child u_c(.a(x), .y(z));\n"
        b"endmodule\n"
    )
    built = ElaboratedWidths.build([path])
    restored = ElaboratedWidths.from_payload(json.loads(json.dumps(built.to_payload())))

    assert len(restored) == len(built) > 0
    assert (restored.file_count, restored.error_count) == (built.file_count, built.error_count)
    assert restored.connection_widths("top", "u_c", "a") == built.connection_widths("top", "u_c", "a") == {(4, 4)}
    assert restored.connection_widths("top", "u_c", "y") == built.connection_widths("top", "u_c", "y") == {(1, 1)}
    text = path.read_text()
    start = text.index("x),")
    assert restored.widths_at(path, start, start + 1) == built.widths_at(path, start, start + 1)
    assert built.widths_at(path, start, start + 1) is not None


@pytest.mark.parametrize("payload", [{}, {"layout": 99}, {"layout": 1}, {"layout": 1, "files": [], "spans": [[0, 1, 2, 0, [1], [0]]], "port_width_pairs": [], "file_count": 0, "error_count": 0}])
def test_a_payload_that_does_not_fit_the_layout_is_refused(payload: dict) -> None:
    with pytest.raises(ValueError):
        ElaboratedWidths.from_payload(payload)


def test_a_version_3_store_gains_the_record_table(tmp_path: Path) -> None:
    store_path = tmp_path / "old.sqlite"
    connection = sqlite3.connect(store_path)
    try:
        connection.executescript(
            """
            CREATE TABLE schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            INSERT INTO schema_meta VALUES ('schema_version', '3');
            """
        )
        connection.commit()
    finally:
        connection.close()

    store = AnalysisStore(store_path)

    assert store.elaboration.count() == 0
    connection = sqlite3.connect(store_path)
    try:
        assert connection.execute("SELECT value FROM schema_meta WHERE key = 'schema_version'").fetchone()[0] == "4"
    finally:
        connection.close()
