"""Implicit real-number/fractional-time-literal-to-integral conversion checks,
for declarator initializers and procedural/continuous assignments."""

import re

from ..syntax_kinds import REAL_LITERAL_EXPRESSION_KIND, REAL_TYPE_KINDS, TIME_LITERAL_EXPRESSION_KIND


def is_fractional_time_literal(text: str, timescale_unit_scale: float = 1e-9) -> bool:
    """Check if a time literal string (e.g. '9.001ns', '9ps') represents a fractional
    number of time units under the given timescale unit."""
    s = text.strip()
    match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)$", s)
    if not match:
        return False
    val_str, unit = match.groups()
    try:
        val = float(val_str)
    except ValueError:
        return False
    scales = {
        "s": 1.0,
        "ms": 1e-3,
        "us": 1e-6,
        "ns": 1e-9,
        "ps": 1e-12,
        "fs": 1e-15,
    }
    unit_scale = scales.get(unit.lower())
    if unit_scale is None:
        return False
    units_count = val * unit_scale / timescale_unit_scale
    return abs(units_count - round(units_count)) > 1e-6


def declarator_is_implicit_real_conversion(raw: object) -> bool:
    """Return True if a declarator initializer converts a real or fractional time literal
    to an integral variable target."""
    parent = getattr(raw, "parent", None)
    type_node = getattr(parent, "type", None)
    type_kind = getattr(type_node, "kind", None)
    if type_kind in REAL_TYPE_KINDS:
        return False

    init = getattr(raw, "initializer", None)
    if init is None:
        return False
    expr = getattr(init, "expr", None)
    if expr is None:
        return False

    expr_kind = getattr(expr, "kind", None)
    if expr_kind == REAL_LITERAL_EXPRESSION_KIND:
        text = str(expr).strip()
        try:
            val = float(text)
            return abs(val - round(val)) > 1e-6
        except ValueError:
            return False

    if expr_kind == TIME_LITERAL_EXPRESSION_KIND:
        text = str(expr).strip()
        return is_fractional_time_literal(text)

    return False


def assignment_is_implicit_real_conversion(raw: object) -> bool:
    """Return True if an assignment right-hand side converts a real literal or fractional
    time literal to an integral target."""
    from ..syntax_queries import assignment_left, assignment_right, is_assignment_expression

    if not is_assignment_expression(raw):
        return False

    left = assignment_left(raw)
    right = assignment_right(raw)
    if left is None or right is None:
        return False

    right_kind = getattr(right, "kind", None)
    if right_kind == REAL_LITERAL_EXPRESSION_KIND:
        text = str(right).strip()
        try:
            val = float(text)
            return abs(val - round(val)) > 1e-6
        except ValueError:
            return False

    if right_kind == TIME_LITERAL_EXPRESSION_KIND:
        text = str(right).strip()
        return is_fractional_time_literal(text)

    right_str = str(right)
    if "$signed(" in right_str or "$unsigned(" in right_str or right_str.startswith("{"):
        for child in getattr(right, "raw_children", getattr(right, "children", [])):
            if getattr(child, "kind", None) == REAL_LITERAL_EXPRESSION_KIND:
                return True

    return False
