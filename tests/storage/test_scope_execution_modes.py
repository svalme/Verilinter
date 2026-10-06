"""Exercise scope semantics across worker serialization and persistent cache reuse."""
import json
import uuid
from pathlib import Path

from src.run_lint import analyze, main


def scratch():
    path = Path(__file__).resolve().parents[1] / "_tmp_cli_execution_modes" / f"scopes_{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    return path


def normalized(rows):
    return sorted(json.dumps(row, sort_keys=True) for row in rows)


def test_expression_and_two_process_fsm_mode_parity():
    root = scratch()
    expression = root / "expression.sv"
    fsm = root / "fsm.sv"
    expression.write_text("""
        module expression(input [7:0] a,b,c, output [7:0] p);
        assign p = a * b + c; endmodule
    """, encoding="utf-8")
    fsm.write_text("""
        module fsm(input clk, rst);
        logic [2:0] state, next_state;
        always @(posedge clk or posedge rst)
            if (rst) state <= 3'b001; else state <= next_state;
        always_comb begin
            next_state = state;
            case (state)
                3'b001: next_state = 3'b010;
                3'b010: next_state = 3'b011;
                3'b011: next_state = 3'b001;
            endcase
        end
        endmodule
    """, encoding="utf-8")
    paths = [expression, fsm]
    reference = analyze(paths, jobs=1, use_cache=False)
    codes = {d["code"] for d in reference.diagnostics}
    assert {"ARITHMETIC_RESULT_TRUNCATION", "MISSING_DEFAULT_ON_STATE_CASE", "ONE_HOT_ENCODING_VIOLATION"} <= codes
    parallel = analyze(paths, jobs=2, use_cache=False)
    cold = analyze(paths, jobs=2, store_path=root / "store.sqlite")
    warm = analyze(paths, jobs=2, store_path=root / "store.sqlite")
    assert cold.cache_stats == {"hits": 0, "misses": 2}
    assert warm.cache_stats == {"hits": 2, "misses": 0}
    for result in (parallel, cold, warm):
        assert normalized(result.diagnostics) == normalized(reference.diagnostics)


def test_cli_parallel_and_cache_equivalence_with_scopes(capsys):
    root = scratch()
    (root / "pkg.sv").write_text("package p; parameter int N = 1; endpackage", encoding="utf-8")
    (root / "top.sv").write_text("""
        module top(output int y);
          import p::*;
          typedef struct packed {int x;} a_t;
          typedef union packed {int x;} b_t;
          function automatic int f(input int x); f = x + N; endfunction
          for(genvar i=0;i<2;i++) begin:g wire x = i; end
          assign y = f(N);
        endmodule
    """, encoding="utf-8")
    common = ["--format", "json", str(root)]
    def run(*options):
        assert main([*common, *options]) == 0
        return json.loads(capsys.readouterr().out)
    reference = run("--jobs", "1", "--no-cache")
    for options in (("--jobs", "4", "--no-cache"),
                    ("--store", str(root / "store.sqlite")),
                    ("--store", str(root / "store.sqlite"))):
        assert normalized(run(*options)) == normalized(reference)
    assert not ({"NO_IMPLICIT_NET", "REDECLARED_VARIABLE", "READ_BEFORE_WRITE"}
                & {row["code"] for row in reference})


def test_package_export_change_invalidates_unchanged_consumer():
    root = scratch()
    package, consumer = root / "pkg.sv", root / "top.sv"
    package.write_text("package p; parameter int N = 1; endpackage", encoding="utf-8")
    consumer.write_text("module m(output int y); import p::*; assign y=N; endmodule", encoding="utf-8")
    paths, store = [consumer, package], root / "store.sqlite"
    first = analyze(paths, store_path=store)
    warm = analyze(paths, store_path=store)
    assert warm.cache_stats == {"hits": 2, "misses": 0}
    package.write_text("package p; parameter int M = 1; endpackage", encoding="utf-8")
    changed = analyze(paths, store_path=store)
    fresh = analyze(paths, use_cache=False)
    assert changed.cache_stats == {"hits": 0, "misses": 2}
    assert normalized(changed.diagnostics) == normalized(fresh.diagnostics)
    assert normalized(changed.diagnostics) != normalized(first.diagnostics)
    assert any(d["code"] == "NO_IMPLICIT_NET" for d in changed.diagnostics)


def test_transitive_include_edit_does_not_reuse_stale_findings():
    root = scratch()
    header, inner, source = root / "outer.svh", root / "inner.svh", root / "top.sv"
    header.write_text('`include "inner.svh"', encoding="utf-8")
    inner.write_text("`define VALUE 1'b0", encoding="utf-8")
    source.write_text('`include "outer.svh"\nmodule m(output y); assign y=`VALUE; endmodule', encoding="utf-8")
    options = dict(store_path=root / "store.sqlite", include_dirs=[str(root)])
    first = analyze([source], **options)
    analyze([source], **options)
    inner.write_text("`define VALUE missing_signal", encoding="utf-8")
    changed = analyze([source], **options)
    fresh = analyze([source], include_dirs=[str(root)], use_cache=False)
    assert changed.cache_stats == {"hits": 0, "misses": 1}
    assert normalized(changed.diagnostics) == normalized(fresh.diagnostics)
    assert normalized(changed.diagnostics) != normalized(first.diagnostics)


def test_include_search_order_is_part_of_cache_key():
    from src.pkg.analysis_store import selection_key
    assert selection_key(None, ["a", "b"]) != selection_key(None, ["b", "a"])


def test_three_tier_transitive_include_edit_invalidates_top():
    root = scratch()
    leaf = root / "leaf.svh"
    mid = root / "mid.svh"
    top_header = root / "top.svh"
    source = root / "top.sv"
    leaf.write_text("`define DEEP_CONST 1'b0", encoding="utf-8")
    mid.write_text('`include "leaf.svh"\n`define MID_CONST `DEEP_CONST', encoding="utf-8")
    top_header.write_text('`include "mid.svh"\n`define TOP_CONST `MID_CONST', encoding="utf-8")
    source.write_text('`include "top.svh"\nmodule m(output y); assign y = `TOP_CONST; endmodule', encoding="utf-8")
    options = dict(store_path=root / "store.sqlite", include_dirs=[str(root)])
    first = analyze([source], **options)
    assert not any(d["code"] == "NO_IMPLICIT_NET" for d in first.diagnostics)
    # Edit the innermost (3rd tier) header
    leaf.write_text("`define DEEP_CONST undeclared_signal", encoding="utf-8")
    changed = analyze([source], **options)
    fresh = analyze([source], include_dirs=[str(root)], use_cache=False)
    assert changed.cache_stats == {"hits": 0, "misses": 1}
    assert normalized(changed.diagnostics) == normalized(fresh.diagnostics)
    assert normalized(changed.diagnostics) != normalized(first.diagnostics)
    assert any(d["code"] == "NO_IMPLICIT_NET" for d in changed.diagnostics)



def test_include_directory_shadowing_e2e():
    root = scratch()
    inc1 = root / "inc1"
    inc2 = root / "inc2"
    inc1.mkdir()
    inc2.mkdir()
    (inc1 / "defs.svh").write_text("`define VALUE 1'b0", encoding="utf-8")
    (inc2 / "defs.svh").write_text("`define VALUE undeclared_signal", encoding="utf-8")
    source = root / "top.sv"
    source.write_text('`include "defs.svh"\nmodule m(output y); assign y = `VALUE; endmodule', encoding="utf-8")
    store = root / "store.sqlite"
    run1 = analyze([source], store_path=store, include_dirs=[str(inc1), str(inc2)])
    assert not any(d["code"] == "NO_IMPLICIT_NET" for d in run1.diagnostics)
    run2 = analyze([source], store_path=store, include_dirs=[str(inc2), str(inc1)])
    assert run2.cache_stats["misses"] == 1
    assert any(d["code"] == "NO_IMPLICIT_NET" for d in run2.diagnostics)
    assert normalized(run1.diagnostics) != normalized(run2.diagnostics)


def test_partial_refresh_callee_port_rename_reconciles_against_cached_caller():
    """Verify that renaming a submodule port causes cross-file rules to fire on an untouched caller in SQLite."""
    root = scratch()
    child, parent = root / "child.sv", root / "parent.sv"
    store = root / "store.sqlite"

    child.write_text("""`timescale 1ns/1ps
module child(
  input logic sys_clk,
  input logic [7:0] din_i,
  output logic [7:0] dout_o
);
  always @(posedge sys_clk) begin
    dout_o <= din_i;
  end
endmodule
""", encoding="utf-8")

    parent.write_text("""`timescale 1ns/1ps
module parent(
  input logic sys_clk,
  input logic [7:0] in_val_i,
  output logic [7:0] out_val_o
);
  child u_child (
    .sys_clk(sys_clk),
    .din_i(in_val_i),
    .dout_o(out_val_o)
  );
endmodule
""", encoding="utf-8")

    paths = [child, parent]
    cold = analyze(paths, store_path=store)
    assert cold.cache_stats == {"hits": 0, "misses": 2}

    warm = analyze(paths, store_path=store)
    assert warm.cache_stats == {"hits": 2, "misses": 0}

    # Rename port din_i -> din_val_i in child module; parent is untouched on disk
    child.write_text("""`timescale 1ns/1ps
module child(
  input logic sys_clk,
  input logic [7:0] din_val_i,
  output logic [7:0] dout_o
);
  always @(posedge sys_clk) begin
    dout_o <= din_val_i;
  end
endmodule
""", encoding="utf-8")

    partial = analyze(paths, store_path=store)
    fresh = analyze(paths, use_cache=False)

    assert partial.cache_stats == {"hits": 1, "misses": 1}
    assert normalized(partial.diagnostics) == normalized(fresh.diagnostics)

    parent_codes = {d["code"] for d in partial.diagnostics if "parent.sv" in d.get("file", "")}
    assert "UNKNOWN_NAMED_PORT_CONNECTION" in parent_codes
    assert "NO_UNCONNECTED_INSTANCE_PORTS" in parent_codes


def test_partial_refresh_caller_variable_rename_preserves_accuracy():
    """Verify that renaming a connecting wire inside a caller module preserves full lint accuracy and parity."""
    root = scratch()
    child, parent = root / "child.sv", root / "parent.sv"
    store = root / "store.sqlite"

    child.write_text("""`timescale 1ns/1ps
module child(
  input logic sys_clk,
  input logic [7:0] din_i,
  output logic [7:0] dout_o
);
  always @(posedge sys_clk) begin
    dout_o <= din_i;
  end
endmodule
""", encoding="utf-8")

    parent.write_text("""`timescale 1ns/1ps
module parent(
  input logic sys_clk,
  input logic [7:0] in_val_i,
  output logic [7:0] out_val_o
);
  wire [7:0] connect_wire;
  assign connect_wire = in_val_i;
  child u_child (
    .sys_clk(sys_clk),
    .din_i(connect_wire),
    .dout_o(out_val_o)
  );
endmodule
""", encoding="utf-8")

    paths = [child, parent]
    cold = analyze(paths, store_path=store)
    assert cold.cache_stats == {"hits": 0, "misses": 2}

    # Rename declaration connect_wire -> renamed_wire in parent, leaving .din_i(connect_wire)
    parent.write_text("""`timescale 1ns/1ps
module parent(
  input logic sys_clk,
  input logic [7:0] in_val_i,
  output logic [7:0] out_val_o
);
  wire [7:0] renamed_wire;
  assign renamed_wire = in_val_i;
  child u_child (
    .sys_clk(sys_clk),
    .din_i(connect_wire),
    .dout_o(out_val_o)
  );
endmodule
""", encoding="utf-8")

    partial = analyze(paths, store_path=store)
    fresh = analyze(paths, use_cache=False)

    assert partial.cache_stats == {"hits": 1, "misses": 1}
    assert normalized(partial.diagnostics) == normalized(fresh.diagnostics)

    parent_codes = {d["code"] for d in partial.diagnostics if "parent.sv" in d.get("file", "")}
    assert "NO_IMPLICIT_NET" in parent_codes
    assert "NO_WRITE_ONLY_VARIABLE" in parent_codes


def test_partial_refresh_caller_edit_preserves_width_and_style_accuracy():
    """Verify that editing a caller with width mismatch and self-assignment preserves exact parity with cold run."""
    root = scratch()
    child, parent = root / "child.sv", root / "parent.sv"
    store = root / "store.sqlite"

    child.write_text("""`timescale 1ns/1ps
module child(
  input logic sys_clk,
  input logic [7:0] din_i,
  output logic [7:0] dout_o
);
  always @(posedge sys_clk) begin
    dout_o <= din_i;
  end
endmodule
""", encoding="utf-8")

    parent.write_text("""`timescale 1ns/1ps
module parent(
  input logic sys_clk,
  input logic [7:0] in_val_i,
  output logic [7:0] out_val_o
);
  child u_child (
    .sys_clk(sys_clk),
    .din_i(in_val_i),
    .dout_o(out_val_o)
  );
endmodule
""", encoding="utf-8")

    paths = [child, parent]
    cold = analyze(paths, store_path=store)
    assert cold.cache_stats == {"hits": 0, "misses": 2}

    # Modify parent to introduce 16-bit to 8-bit width mismatch and self-assignment
    parent.write_text("""`timescale 1ns/1ps
module parent(
  input logic sys_clk,
  input logic [15:0] in_val_i,
  output logic [7:0] out_val_o
);
  logic [7:0] loop_sig;
  assign loop_sig = loop_sig;
  child u_child (
    .sys_clk(sys_clk),
    .din_i(in_val_i),
    .dout_o(out_val_o)
  );
endmodule
""", encoding="utf-8")

    partial = analyze(paths, store_path=store)
    fresh = analyze(paths, use_cache=False)

    assert partial.cache_stats == {"hits": 1, "misses": 1}
    assert normalized(partial.diagnostics) == normalized(fresh.diagnostics)

    parent_codes = {d["code"] for d in partial.diagnostics if "parent.sv" in d.get("file", "")}
    assert "PORT_CONNECTION_WIDTH_MISMATCH" in parent_codes
    assert "NO_SELF_ASSIGNMENT" in parent_codes


def test_partial_refresh_duplicate_module_cross_file_accuracy():
    """Verify that renaming a module to collide with an untouched module cached in SQLite raises DUPLICATE_MODULE."""
    root = scratch()
    mod_a, mod_b = root / "mod_a.sv", root / "mod_b.sv"
    store = root / "store.sqlite"

    mod_a.write_text("`timescale 1ns/1ps\nmodule worker_a(input clk); endmodule\n", encoding="utf-8")
    mod_b.write_text("`timescale 1ns/1ps\nmodule worker_b(input clk); endmodule\n", encoding="utf-8")

    paths = [mod_a, mod_b]
    cold = analyze(paths, store_path=store)
    assert cold.cache_stats == {"hits": 0, "misses": 2}

    # Rename worker_b -> worker_a in mod_b.sv; mod_a.sv is untouched on disk
    mod_b.write_text("`timescale 1ns/1ps\nmodule worker_a(input clk); endmodule\n", encoding="utf-8")

    partial = analyze(paths, store_path=store)
    fresh = analyze(paths, use_cache=False)

    assert partial.cache_stats == {"hits": 1, "misses": 1}
    assert normalized(partial.diagnostics) == normalized(fresh.diagnostics)

    codes = {d["code"] for d in partial.diagnostics}
    assert "DUPLICATE_MODULE" in codes



