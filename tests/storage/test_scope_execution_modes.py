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
    from pkg.analysis_store import selection_key
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


