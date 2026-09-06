import pyslang as sl

from ..syntax_kinds import (
    ALIAS_STATEMENT_KIND,
    ALWAYS_COMB_BLOCK_KIND,
    ALWAYS_FF_BLOCK_KIND,
    ALWAYS_LATCH_BLOCK_KIND,
    BIND_DIRECTIVE_KIND,
    CHANDLE_TYPE_KIND,
    CHECKER_DECLARATION_KIND,
    CLASS_DECLARATION_KIND,
    CLOCKING_DECLARATION_KIND,
    CONFIG_DECLARATION_KIND,
    COVERGROUP_DECLARATION_KIND,
    DPI_IMPORT_EXPORT_KINDS,
    EXPECT_RESTRICT_PROPERTY_KINDS,
    FINAL_BLOCK_KIND,
    FUNCTION_DECLARATION_KIND,
    INITIAL_BLOCK_KIND,
    INTERFACE_DECLARATION_KIND,
    LET_DECLARATION_KIND,
    LOOP_GENERATE_KIND,
    MODPORT_DECLARATION_KIND,
    PACKAGE_DECLARATION_KIND,
    PRIMITIVE_DECLARATION_KIND,
    PROGRAM_DECLARATION_KIND,
    PROPERTY_DECLARATION_KIND,
    QUEUE_DIMENSION_SPECIFIER_KIND,
    RANDSEQUENCE_STATEMENT_KIND,
    RANGE_DIMENSION_SPECIFIER_KIND,
    REAL_TYPE_KINDS,
    SEQUENCE_DECLARATION_KIND,
    SPECIFY_BLOCK_KIND,
    STRING_TYPE_KIND,
    TASK_DECLARATION_KIND,
    VARIABLE_DIMENSION_KIND,
    VIRTUAL_INTERFACE_TYPE_KIND,
    WILDCARD_DIMENSION_SPECIFIER_KIND,
)
from ..types import CaseGenerateNode, IfGenerateNode, LoopGenerateNode


def is_initial_block(raw: object) -> bool:
    return getattr(raw, "kind", None) == INITIAL_BLOCK_KIND


def is_final_block(raw: object) -> bool:
    return getattr(raw, "kind", None) == FINAL_BLOCK_KIND


def is_always_latch_block(raw: object) -> bool:
    return getattr(raw, "kind", None) == ALWAYS_LATCH_BLOCK_KIND


def is_always_ff_block(raw: object) -> bool:
    return getattr(raw, "kind", None) == ALWAYS_FF_BLOCK_KIND


def is_always_comb_block(raw: object) -> bool:
    return getattr(raw, "kind", None) == ALWAYS_COMB_BLOCK_KIND


def is_case_generate_node(raw: object) -> bool:
    return isinstance(raw, CaseGenerateNode)


def is_checker_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == CHECKER_DECLARATION_KIND


def is_clocking_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == CLOCKING_DECLARATION_KIND


def is_interface_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == INTERFACE_DECLARATION_KIND


def is_modport_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == MODPORT_DECLARATION_KIND


def is_loop_generate_node(raw: object) -> bool:
    return isinstance(raw, LoopGenerateNode) or getattr(raw, "kind", None) == LOOP_GENERATE_KIND


def is_if_generate_node(raw: object) -> bool:
    return isinstance(raw, IfGenerateNode) or getattr(raw, "kind", None) == getattr(sl.SyntaxKind, "IfGenerate", None)


def is_task_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == TASK_DECLARATION_KIND


def is_function_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == FUNCTION_DECLARATION_KIND


def is_class_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == CLASS_DECLARATION_KIND


def is_covergroup_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == COVERGROUP_DECLARATION_KIND


def is_sequence_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == SEQUENCE_DECLARATION_KIND


def is_property_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == PROPERTY_DECLARATION_KIND


def is_let_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == LET_DECLARATION_KIND


def is_config_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == CONFIG_DECLARATION_KIND


def is_randsequence_statement_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == RANDSEQUENCE_STATEMENT_KIND


def is_expect_restrict_property_node(raw: object) -> bool:
    return getattr(raw, "kind", None) in EXPECT_RESTRICT_PROPERTY_KINDS


def is_virtual_interface_type_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == VIRTUAL_INTERFACE_TYPE_KIND


def is_dpi_import_export_node(raw: object) -> bool:
    return getattr(raw, "kind", None) in DPI_IMPORT_EXPORT_KINDS


def is_real_type_node(raw: object) -> bool:
    return getattr(raw, "kind", None) in REAL_TYPE_KINDS


def is_string_type_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == STRING_TYPE_KIND


def is_chandle_type_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == CHANDLE_TYPE_KIND


def is_dynamic_array_dimension_node(raw: object) -> bool:
    """True for a bare `[]` dimension (`int arr[];`) -- a dynamic array. The same
    `VariableDimensionSyntax` node is used for every unpacked dimension form; a
    dynamic array is the one with no `specifier` child at all (contrast a fixed
    size `[4]`, a range `[3:0]`, a queue `[$]`, or an associative index `[string]`,
    all of which populate `specifier`)."""
    return getattr(raw, "kind", None) == VARIABLE_DIMENSION_KIND and getattr(raw, "specifier", None) is None


def is_queue_dimension_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == QUEUE_DIMENSION_SPECIFIER_KIND


def is_associative_array_dimension_node(raw: object) -> bool:
    """True for an associative-array dimension: a wildcard index (`arr[*]`), or an
    explicit built-in-type index (`arr[string]`, `arr[int]`, `arr[byte]`, ...).

    A user-defined-type index (`arr[my_type_t]`) is deliberately NOT recognized:
    it parses as an ordinary `IdentifierNameSyntax` under the same
    `RangeDimensionSpecifier` -> `BitSelect` shape as a perfectly ordinary
    parameter-sized fixed array (`arr[WIDTH]`), and telling the two apart needs
    type/symbol resolution this syntax-only check doesn't have -- guessing would
    misfire on completely ordinary, rule-compliant RTL. `sl.DataTypeSyntax` is the
    real discriminator for the recognized cases: a dimension index is always an
    expression syntactically, so a genuine type-keyword node there (`KeywordTypeSyntax`
    for `string`, `IntegerTypeSyntax` for `int`/`byte`/`bit`/...) is unambiguous.
    """
    kind = getattr(raw, "kind", None)
    if kind == WILDCARD_DIMENSION_SPECIFIER_KIND:
        return True
    if kind != RANGE_DIMENSION_SPECIFIER_KIND:
        return False
    selector = getattr(raw, "selector", None)
    index_expr = getattr(selector, "expr", None)
    return isinstance(index_expr, sl.DataTypeSyntax)


def is_program_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == PROGRAM_DECLARATION_KIND


def is_package_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == PACKAGE_DECLARATION_KIND


def is_specify_block_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == SPECIFY_BLOCK_KIND


def is_primitive_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == PRIMITIVE_DECLARATION_KIND


def is_alias_statement_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == ALIAS_STATEMENT_KIND


def is_bind_directive_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == BIND_DIRECTIVE_KIND
