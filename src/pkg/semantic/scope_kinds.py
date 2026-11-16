"""Which syntax constructs open a scope, and of what kind.

The table is the single record of scope shape. Handlers take the scope kind from `ScopeKind`, rules
compare against `ScopeKind`, and `tests/semantic/test_scope_policy.py` walks every entry's sample so a
construct that should open a scope but does not is a recorded gap, not a silent omission.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ScopeKind(StrEnum):
    """Values equal the plain strings older code compared against."""

    GLOBAL = "global"
    MODULE = "module"
    PACKAGE = "package"
    FUNCTION = "function"
    TASK = "task"
    FOR = "for"
    GENERATE_FOR = "generate_for"
    GENERATE_BLOCK = "generate_block"
    BLOCK = "block"  # a begin-end or fork-join block that declares a variable of its own
    AGGREGATE = "aggregate"


SUBROUTINE_SCOPE_KINDS = frozenset({ScopeKind.FUNCTION, ScopeKind.TASK})

# Scopes that own the names declared for them by default (implicit nets). Generate, loop and aggregate
# scopes are inside one of these, and an implicit net belongs to the enclosing one, not to the block.
NAME_OWNING_SCOPE_KINDS = frozenset(
    {ScopeKind.GLOBAL, ScopeKind.MODULE, ScopeKind.PACKAGE, ScopeKind.FUNCTION, ScopeKind.TASK}
)


@dataclass(frozen=True)
class ScopePolicyEntry:
    """One construct (or family sharing a handler) and whether it opens a scope.

    `sample` holds two sibling constructs that each declare `qq_dup`. When the construct opens its own
    scope the two declarations are unrelated; when it does not, they collide as a redeclaration.
    """

    constructs: tuple[str, ...]  # pyslang SyntaxKind names
    scope_kind: ScopeKind | None  # None for a construct that opens no scope yet
    sample: str
    note: str = ""

    @property
    def is_gap(self) -> bool:
        return self.scope_kind is None


SCOPE_POLICY: tuple[ScopePolicyEntry, ...] = (
    ScopePolicyEntry(
        ("ModuleDeclaration", "InterfaceDeclaration", "ProgramDeclaration"),
        ScopeKind.MODULE,
        "module a; logic qq_dup; endmodule\nmodule b; logic qq_dup; endmodule",
    ),
    ScopePolicyEntry(
        ("PackageDeclaration",),
        ScopeKind.PACKAGE,
        "package a; int qq_dup; endpackage\npackage b; int qq_dup; endpackage",
    ),
    ScopePolicyEntry(
        ("FunctionDeclaration",),
        ScopeKind.FUNCTION,
        "module m;\n function automatic void f1; int qq_dup; endfunction\n function automatic void f2; int qq_dup; endfunction\nendmodule",
    ),
    ScopePolicyEntry(
        ("TaskDeclaration",),
        ScopeKind.TASK,
        "module m;\n task automatic t1; int qq_dup; endtask\n task automatic t2; int qq_dup; endtask\nendmodule",
    ),
    ScopePolicyEntry(
        ("ForLoopStatement",),
        ScopeKind.FOR,
        "module m; initial begin\n for (int qq_dup = 0; qq_dup < 1; qq_dup++) ;\n for (int qq_dup = 0; qq_dup < 1; qq_dup++) ;\nend endmodule",
    ),
    ScopePolicyEntry(
        ("LoopGenerate",),
        ScopeKind.GENERATE_FOR,
        "module m; genvar i, j;\n for (i = 0; i < 1; i++) begin : g1 wire qq_dup; end\n for (j = 0; j < 1; j++) begin : g2 wire qq_dup; end\nendmodule",
    ),
    ScopePolicyEntry(
        ("GenerateBlock",),
        ScopeKind.GENERATE_BLOCK,
        "module m #(parameter T = 1);\n if (T > 1) begin : g1 wire qq_dup; end else begin : g2 wire qq_dup; end\nendmodule",
    ),
    ScopePolicyEntry(
        ("StructType", "UnionType"),
        ScopeKind.AGGREGATE,
        "module m; struct packed {logic qq_dup;} s1; struct packed {logic qq_dup;} s2; endmodule",
    ),
    ScopePolicyEntry(
        ("SequentialBlockStatement", "ParallelBlockStatement"),
        ScopeKind.BLOCK,
        "module m;\n initial begin : b1 int qq_dup; end\n initial begin : b2 int qq_dup; end\nendmodule",
        "a begin-end or fork-join block opens a scope only when it declares a variable of its own",
    ),
    # Constructs that are namespaces in IEEE 1800 but open no scope here. Each is a known gap.
    ScopePolicyEntry(
        ("ClassDeclaration",),
        None,
        "module m;\n class c1; int qq_dup; endclass\n class c2; int qq_dup; endclass\nendmodule",
        "classes are outside the supported RTL subset",
    ),
    ScopePolicyEntry(
        ("CheckerDeclaration",),
        None,
        "checker c1; int qq_dup; endchecker\nchecker c2; int qq_dup; endchecker",
        "checkers are outside the supported RTL subset",
    ),
)


def scope_kind_for_construct(construct: str) -> ScopeKind | None:
    for entry in SCOPE_POLICY:
        if construct in entry.constructs:
            return entry.scope_kind
    return None
