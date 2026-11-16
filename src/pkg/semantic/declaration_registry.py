"""Which syntax constructs declare a name, and how each one is covered.

A construct that declares a name but has no coverage here falls through to the identifier resolver and is
reported as an implicit net or an undeclared variable. This table is the one place that says how each
declaration-shaped construct is covered. `tests/semantic/test_declaration_registry.py` checks that every
declaration-shaped `SyntaxKind` pyslang defines appears here, that each handler named here is registered,
and that each sample behaves as its entry says, so a new or missing construct fails a test.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .symbol_kind import SymbolKind


class Coverage(StrEnum):
    HANDLER = "handler"  # a registered handler declares the name
    GENERIC = "generic"  # the name resolves through a generic path (the declarator handler, enum members, ...)
    GAP = "gap"  # the construct declares a name that does not resolve yet
    NOT_APPLICABLE = "not_applicable"  # declares no name usable in RTL expressions, or is outside the supported subset


@dataclass(frozen=True)
class DeclarationEntry:
    """One construct (or family sharing coverage) that declares a name.

    `sample` is a module-level source snippet that declares `qq_x` with the construct and uses it. It is
    parsed with `default_nettype none`, where an unresolved `qq_x` is reported. Samples are required for
    HANDLER, GENERIC and GAP entries.
    """

    kinds: tuple[str, ...]  # pyslang SyntaxKind names
    coverage: Coverage
    handler: str | None = None  # registered handler class name, for HANDLER entries
    declares_kind: SymbolKind | None = None  # Symbol.kind the construct produces, when it produces a symbol of the name
    sample: str | None = None
    note: str = ""


DECLARATIONS: tuple[DeclarationEntry, ...] = (
    # --- explicit handlers ---
    DeclarationEntry(
        ("ModuleDeclaration", "InterfaceDeclaration", "ProgramDeclaration", "PackageDeclaration"),
        Coverage.HANDLER,
        "ModuleDeclarationHandler",
        sample="module qq_x; endmodule",
        note="module, interface, program and package names are registered as scopes, not as symbols",
    ),
    DeclarationEntry(
        ("FunctionDeclaration", "TaskDeclaration"),
        Coverage.HANDLER,
        "FunctionDeclarationHandler",
        sample="module m; function automatic int qq_x(int a); return a; endfunction wire [3:0] w = qq_x(1); endmodule",
    ),
    DeclarationEntry(
        ("TypedefDeclaration", "ForwardTypedefDeclaration"),
        Coverage.HANDLER,
        "TypedefDeclarationHandler",
        declares_kind=SymbolKind.TYPEDEF,
        sample="module m; typedef logic [3:0] qq_x; qq_x v; endmodule",
    ),
    DeclarationEntry(
        ("GenvarDeclaration",),
        Coverage.HANDLER,
        "GenvarDeclarationHandler",
        declares_kind=SymbolKind.GENVAR,
        sample="module m; genvar qq_x; for (qq_x = 0; qq_x < 2; qq_x = qq_x + 1) begin : g end endmodule",
    ),
    DeclarationEntry(
        ("TypeParameterDeclaration", "TypeAssignment"),
        Coverage.HANDLER,
        "TypeParameterDeclarationHandler",
        declares_kind=SymbolKind.TYPEDEF,
        sample="module m #(parameter type qq_x = logic); qq_x v; endmodule",
    ),
    DeclarationEntry(
        ("PackageImportDeclaration",),
        Coverage.HANDLER,
        "PackageImportHandler",
        sample="package p; localparam int qq_x = 1; endpackage\nmodule m; import p::*; wire [qq_x:0] w; endmodule",
    ),
    DeclarationEntry(
        ("UdpDeclaration",),
        Coverage.HANDLER,
        "PrimitiveDeclarationHandler",
        sample="primitive qq_x (output o, input a); table 0 : 0; 1 : 1; endtable endprimitive\nmodule m; wire o, a; qq_x u (o, a); endmodule",
    ),
    DeclarationEntry(
        ("Declarator",),
        Coverage.HANDLER,
        "DeclaratorHandler",
        sample="module m; logic qq_x; initial qq_x = 1'b0; endmodule",
        note="every variable, net, port and parameter name goes through this handler; the entries below are the declaring constructs around it",
    ),
    # --- names introduced through the generic declarator path ---
    DeclarationEntry(
        ("DataDeclaration", "LocalVariableDeclaration", "ForVariableDeclaration"),
        Coverage.GENERIC,
        sample="module m; logic qq_x; initial qq_x = 1'b0; initial for (int qq_y = 0; qq_y < 2; qq_y++) ; endmodule",
    ),
    DeclarationEntry(
        ("NetDeclaration",),
        Coverage.GENERIC,
        sample="module m; wire [3:0] qq_x; assign qq_x = 4'd0; endmodule",
    ),
    DeclarationEntry(
        ("ImplicitAnsiPort", "ExplicitAnsiPort", "VariablePortHeader", "NetPortHeader"),
        Coverage.GENERIC,
        sample="module m(input logic qq_x); wire w = qq_x; endmodule",
    ),
    DeclarationEntry(
        ("PortDeclaration", "ImplicitNonAnsiPort", "ExplicitNonAnsiPort", "EmptyNonAnsiPort"),
        Coverage.GENERIC,
        sample="module m(qq_x); input qq_x; wire w = qq_x; endmodule",
    ),
    DeclarationEntry(
        ("ParameterDeclaration",),
        Coverage.GENERIC,
        sample="module m #(parameter int qq_x = 1); localparam int qq_y = 2; wire [qq_x:0] w; wire [qq_y:0] v; endmodule",
    ),
    DeclarationEntry(
        ("FunctionPort", "DefaultFunctionPort"),
        Coverage.GENERIC,
        sample="module m; function automatic int f(int qq_x); return qq_x; endfunction endmodule",
    ),
    DeclarationEntry(
        ("NetTypeDeclaration",),
        Coverage.GENERIC,
        sample="module m; nettype logic qq_x; qq_x v; endmodule",
    ),
    DeclarationEntry(
        ("ModportDeclaration", "ModportNamedPort", "ModportExplicitPort"),
        Coverage.GENERIC,
        sample="interface i; logic s; modport qq_x(input s); endinterface\nmodule m(i.qq_x p); endmodule",
    ),
    DeclarationEntry(
        ("EnumType",),
        Coverage.GENERIC,
        sample="module m; typedef enum logic {qq_x, QQ_B} e_t; e_t v = qq_x; endmodule",
        note="not matched by the declaration-shaped pattern; listed because enum members declare names",
    ),
    DeclarationEntry(
        ("HierarchyInstantiation",),
        Coverage.HANDLER,
        "HierarchyInstantiationHandler",
        sample="module c; endmodule\nmodule m; c qq_x(); endmodule",
        note="instance names; not matched by the declaration-shaped pattern",
    ),
    # --- names that do not resolve yet ---
    DeclarationEntry(
        ("ClockingDeclaration",),
        Coverage.GAP,
        "ClockingDeclarationHandler",
        sample="module m(input logic clk); clocking qq_x @(posedge clk); endclocking initial @(qq_x); endmodule",
        note="the handler registers the clocking signals but not the clocking block's own name",
    ),
    DeclarationEntry(
        ("LetDeclaration",),
        Coverage.GAP,
        sample="module m; let qq_x = 1; wire w = qq_x; endmodule",
    ),
    DeclarationEntry(
        ("SpecparamDeclaration", "SpecparamDeclarator"),
        Coverage.GAP,
        sample="module m; specparam qq_x = 1; wire [qq_x:0] w; endmodule",
    ),
    DeclarationEntry(
        ("SequenceDeclaration",),
        Coverage.GAP,
        sample="module m(input logic clk, a); sequence qq_x; a; endsequence assert property (@(posedge clk) qq_x); endmodule",
    ),
    DeclarationEntry(
        ("PropertyDeclaration",),
        Coverage.GAP,
        sample="module m(input logic clk, a); property qq_x; a; endproperty assert property (@(posedge clk) qq_x); endmodule",
    ),
    DeclarationEntry(
        ("GenerateBlock",),
        Coverage.NOT_APPLICABLE,
        note="a generate block label only appears as the first segment of a hierarchical path, and the resolver treats an undeclared path base as unresolvable here, so no symbol is needed",
    ),
    # --- constructs that declare no name usable in RTL expressions, or are outside the supported subset ---
    DeclarationEntry(
        ("ClassDeclaration", "ClassMethodDeclaration", "ClassPropertyDeclaration", "ConstraintDeclaration", "CovergroupDeclaration", "CheckerDeclaration", "CheckerDataDeclaration", "AssertionItemPort"),
        Coverage.NOT_APPLICABLE,
        note="class, constraint, covergroup and checker constructs are outside the supported RTL subset",
    ),
    DeclarationEntry(
        ("ModportClockingPort", "ModportSubroutinePort"),
        Coverage.NOT_APPLICABLE,
        note="modport clocking and import/export ports reference names declared elsewhere",
    ),
    DeclarationEntry(
        ("ModuleHeader", "PackageHeader", "ProgramHeader", "InterfaceHeader", "InterfacePortHeader"),
        Coverage.NOT_APPLICABLE,
        note="headers carry the port and parameter lists; the names are declared by the entries above",
    ),
    DeclarationEntry(
        ("NamedParamAssignment", "OrderedParamAssignment", "ParameterValueAssignment", "DefParamAssignment"),
        Coverage.NOT_APPLICABLE,
        note="assignments to parameters declared elsewhere",
    ),
    DeclarationEntry(
        ("PackageExportDeclaration", "PackageExportAllDeclaration"),
        Coverage.NOT_APPLICABLE,
        note="re-exports of names declared elsewhere",
    ),
    DeclarationEntry(
        ("PathDeclaration", "ConditionalPathDeclaration", "IfNonePathDeclaration", "PulseStyleDeclaration", "TimeUnitsDeclaration", "DefaultDisableDeclaration"),
        Coverage.NOT_APPLICABLE,
        note="timing, specify-block and default declarations introduce no names",
    ),
    DeclarationEntry(
        ("LibraryDeclaration", "ConfigDeclaration", "UserDefinedNetDeclaration"),
        Coverage.NOT_APPLICABLE,
        note="library, configuration and user-defined net-type constructs are not part of module RTL",
    ),
)


def entry_for_kind(kind: str) -> DeclarationEntry | None:
    for entry in DECLARATIONS:
        if kind in entry.kinds:
            return entry
    return None
