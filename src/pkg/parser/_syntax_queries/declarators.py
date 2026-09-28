"""Declarator/port metadata queries: name, initializer, kind (port/parameter/
localparam), direction, packed/unpacked dimensions, bit width, signedness,
and clocking-declaration signal extraction."""

from ..syntax_kinds import (
    ALL_PORT_DECLARATION_KINDS,
    ANSI_PORT_KINDS,
    CLOCKING_DECLARATION_KIND,
    DATA_DECLARATION_KINDS,
    ENUM_TYPE_KIND,
    EVENT_TYPE_KIND,
    FUNCTION_PORT_KIND,
    IMPLICIT_TYPE_KIND,
    LOCALPARAM_TOKEN_KIND,
    NET_DECLARATION_KINDS,
    PARAMETER_DECLARATION_KIND,
    PARAMETER_DECLARATION_KINDS,
    PARAMETER_DECLARATION_STATEMENT_KIND,
    PORT_DECLARATION_KIND,
    PORT_DIRECTION_TOKEN_KINDS,
)
from ..types import SyntaxNode, SyntaxTree
from .shared import identifier_name, node_location, source_text_for_node


def declarator_name(raw: object) -> str | None:
    name = getattr(raw, "name", None)
    value = getattr(name, "value", None)
    return value if isinstance(value, str) and value else None


def declarator_has_initializer(raw: object) -> bool:
    return getattr(raw, "initializer", None) is not None


def declarator_initializer_value(raw: object, scope: object = None) -> int | None:
    """Return a declarator's initializer expression constant-folded to an
    `int` (via `evaluate_constant_expression`), else `None` -- used to populate
    `Symbol.value` for `parameter`/`localparam` declarators whose RHS is a
    resolvable constant expression."""
    from ..syntax_queries import evaluate_constant_expression

    initializer = getattr(raw, "initializer", None)
    expr = getattr(initializer, "expr", None)
    if expr is None:
        return None
    return evaluate_constant_expression(expr, scope=scope)


def declarator_initializer_expression(raw: object) -> SyntaxNode | None:
    initializer = getattr(raw, "initializer", None)
    expr = getattr(initializer, "expr", None)
    return expr if isinstance(expr, SyntaxNode) else None



def declarator_is_port(ctx: "Context") -> bool:
    for ancestor in reversed(ctx.stack):
        raw = ancestor.raw
        kind = getattr(raw, "kind", None)
        if kind in ALL_PORT_DECLARATION_KINDS:
            return True
        if kind in DATA_DECLARATION_KINDS:
            return False
    return False


def declarator_is_parameter(ctx: "Context") -> bool:
    """True if the declarator being processed belongs to a `parameter`/`localparam`
    declaration (`ParameterDeclarationSyntax`) rather than an ordinary net/variable
    declaration or a port. Both `parameter` and `localparam` share this same node
    kind -- pyslang distinguishes them only via the declaration's own `keyword`
    field, which this project's rules have no current need to tell apart."""
    for ancestor in reversed(ctx.stack):
        raw = ancestor.raw
        kind = getattr(raw, "kind", None)
        if kind in PARAMETER_DECLARATION_KINDS:
            return True
        if (
            kind in DATA_DECLARATION_KINDS
            or kind in ALL_PORT_DECLARATION_KINDS
            or kind in NET_DECLARATION_KINDS
        ):
            return False
    return False


def declarator_is_enum_member(ctx: "Context") -> bool:
    """True if the declarator being processed belongs to an `enum` definition
    (`EnumTypeSyntax`) rather than an ordinary variable/signal declaration."""
    for ancestor in reversed(ctx.stack):
        raw = ancestor.raw
        kind = getattr(raw, "kind", None)
        if kind == ENUM_TYPE_KIND:
            return True
        if (
            kind in DATA_DECLARATION_KINDS
            or kind in PARAMETER_DECLARATION_KINDS
            or kind in ALL_PORT_DECLARATION_KINDS
            or kind in NET_DECLARATION_KINDS
        ):
            return False
    return False


def declarator_is_localparam(ctx: "Context") -> bool:
    """True if the declarator being processed belongs to a `localparam` declaration."""
    for ancestor in reversed(ctx.stack):
        raw = ancestor.raw
        kind = getattr(raw, "kind", None)
        if kind == PARAMETER_DECLARATION_STATEMENT_KIND:
            param = getattr(raw, "parameter", None)
            kw = getattr(param, "keyword", None)
            if getattr(kw, "kind", None) == LOCALPARAM_TOKEN_KIND:
                return True
        elif kind == PARAMETER_DECLARATION_KIND:
            kw = getattr(raw, "keyword", None)
            if getattr(kw, "kind", None) == LOCALPARAM_TOKEN_KIND:
                return True
        if (
            kind in DATA_DECLARATION_KINDS
            or kind in ALL_PORT_DECLARATION_KINDS
            or kind in NET_DECLARATION_KINDS
        ):
            return False
    return False


def _explicit_port_direction(raw: object) -> str | None:
    header = getattr(raw, "header", None)
    direction = getattr(header, "direction", None)
    return PORT_DIRECTION_TOKEN_KINDS.get(getattr(direction, "kind", None))


def _ansi_port_list_items(list_node: object) -> list[object]:
    """Flatten an `AnsiPortListSyntax` down to its ordered `ImplicitAnsiPortSyntax`
    items, looking through the intermediate separated-list wrapper pyslang puts
    between the list and its items."""
    items: list[object] = []
    visited: set[int] = set()

    def _walk(node: object, depth: int = 0) -> None:
        if depth >= 64 or node is None:
            return
        nid = id(node)
        if nid in visited:
            return
        visited.add(nid)

        try:
            children = iter(node)
        except TypeError:
            return

        for child in children:
            if not isinstance(child, SyntaxNode):
                continue
            if getattr(child, "kind", None) in ANSI_PORT_KINDS:
                items.append(child)
            else:
                _walk(child, depth + 1)

    _walk(list_node)
    return items


def _inherited_port_direction(raw: object) -> str | None:
    """A port that omits its own direction keyword (`input clk, wen,` -- `wen`
    has no keyword of its own) inherits the *previous* port's direction in the
    same ANSI port list. pyslang models this literally: `wen`'s own
    `ImplicitAnsiPortSyntax.header.direction` is an empty token, not a copy of
    `clk`'s. This scans
    backward through the enclosing port list's ordered items for the nearest
    preceding one that does carry an explicit direction."""
    parent = getattr(raw, "parent", None)
    if parent is None:
        return None
    siblings = _ansi_port_list_items(parent)
    try:
        index = next(i for i, sibling in enumerate(siblings) if sibling is raw)
    except StopIteration:
        return None
    for sibling in reversed(siblings[:index]):
        direction = _explicit_port_direction(sibling)
        if direction is not None:
            return direction
    return None


def declarator_port_direction(ctx: "Context") -> str | None:
    """Return "input" / "output" / "inout" / "ref" for a port declarator, else
    None. Falls back to `_inherited_port_direction` for an ANSI port that
    shares a preceding port's direction keyword instead of repeating it."""
    for ancestor in reversed(ctx.stack):
        raw = ancestor.raw
        kind = getattr(raw, "kind", None)
        if kind == FUNCTION_PORT_KIND:
            # Function/task ANSI arguments default to input and inherit omitted
            # directions from earlier arguments in the same prototype.
            direction = "input"
            parent = getattr(raw, "parent", None)
            ports = getattr(parent, "ports", None) or ()
            for port in ports:
                if getattr(port, "kind", None) != FUNCTION_PORT_KIND:
                    continue
                dir_tok = getattr(port, "direction", None)
                direction = PORT_DIRECTION_TOKEN_KINDS.get(getattr(dir_tok, "kind", None), direction)
                if port is raw:
                    return direction
            return direction
        if kind in ANSI_PORT_KINDS or kind == PORT_DECLARATION_KIND:
            direction = _explicit_port_direction(raw)
            if direction is not None:
                return direction
            return _inherited_port_direction(raw)
        if kind in DATA_DECLARATION_KINDS:
            return None
    return None


def declarator_is_event(ctx: "Context") -> bool:
    """True if the declarator's declared data type is `event`."""
    if EVENT_TYPE_KIND is None:
        return False
    for ancestor in reversed(ctx.stack):
        raw = ancestor.raw
        kind = getattr(raw, "kind", None)
        if kind in DATA_DECLARATION_KINDS or kind in NET_DECLARATION_KINDS:
            dt = getattr(raw, "type", None)
            if dt is not None and getattr(dt, "kind", None) == EVENT_TYPE_KIND:
                return True
        elif kind in ANSI_PORT_KINDS or kind == PORT_DECLARATION_KIND:
            header = getattr(raw, "header", None)
            if header is not None:
                dt = getattr(header, "dataType", None)
                if dt is not None and getattr(dt, "kind", None) == EVENT_TYPE_KIND:
                    return True
    return False


def _declarator_owner_packed_dimensions(ctx: "Context") -> list[SyntaxNode]:
    for ancestor in reversed(ctx.stack):
        raw = ancestor.raw
        kind = getattr(raw, "kind", None)
        if kind in ANSI_PORT_KINDS or kind == PORT_DECLARATION_KIND:
            header = getattr(raw, "header", None)
            if header is not None:
                dt = getattr(header, "dataType", None)
                if dt is not None and hasattr(dt, "dimensions"):
                    dims = [d for d in dt.dimensions if isinstance(d, SyntaxNode)]
                    if dims:
                        return dims
        elif kind in DATA_DECLARATION_KINDS or kind in NET_DECLARATION_KINDS:
            dt = getattr(raw, "type", None)
            if dt is not None and hasattr(dt, "dimensions"):
                dims = [d for d in dt.dimensions if isinstance(d, SyntaxNode)]
                if dims:
                    return dims
        elif kind in PARAMETER_DECLARATION_KINDS:
            dt = getattr(raw, "type", None)
            if dt is not None and hasattr(dt, "dimensions"):
                dims = [d for d in dt.dimensions if isinstance(d, SyntaxNode)]
                if dims:
                    return dims
    return []


def declarator_packed_dimension_texts(ctx: "Context", tree: SyntaxTree | None) -> list[tuple[str, str]]:
    """Return [(msb_text, lsb_text), ...] raw text representation of packed dimensions
    for the declarator, or [] if scalar or dimensionless."""
    dims = _declarator_owner_packed_dimensions(ctx)
    result: list[tuple[str, str]] = []
    for dim in dims:
        spec = getattr(dim, "specifier", None)
        selector = getattr(spec, "selector", None)
        if selector is not None:
            left = getattr(selector, "left", None)
            right = getattr(selector, "right", None)
            if left is not None and right is not None:
                left_text = source_text_for_node(left, tree)
                right_text = source_text_for_node(right, tree)
                if left_text and right_text:
                    result.append((left_text.strip(), right_text.strip()))
    return result


def declarator_packed_dimension_widths(ctx: "Context") -> list[int | None]:
    """Return [width, ...] for each packed dimension of the declarator."""
    dims = _declarator_owner_packed_dimensions(ctx)
    if not dims:
        return []
    from ..syntax_queries import evaluate_constant_expression

    scope = getattr(ctx, "scope", lambda: None)()
    result: list[int | None] = []
    for dim in dims:
        spec = getattr(dim, "specifier", None)
        selector = getattr(spec, "selector", None)
        dim_w = None
        if selector is not None:
            left = getattr(selector, "left", None)
            right = getattr(selector, "right", None)
            if left is not None and right is not None:
                msb = evaluate_constant_expression(left, scope=scope)
                lsb = evaluate_constant_expression(right, scope=scope)
                if msb is not None and lsb is not None:
                    dim_w = abs(msb - lsb) + 1
        result.append(dim_w)
    return result


def declarator_unpacked_dimension_texts(raw: object, tree: SyntaxTree | None) -> list[tuple[str, str]]:
    """Return [(msb_text, lsb_text), ...] raw text representation of unpacked dimensions
    for the declarator, or [] if non-array."""
    dims = getattr(raw, "dimensions", None)
    if not dims:
        return []
    result: list[tuple[str, str]] = []
    for dim in dims:
        spec = getattr(dim, "specifier", None)
        selector = getattr(spec, "selector", None)
        if selector is not None:
            left = getattr(selector, "left", None)
            right = getattr(selector, "right", None)
            if left is not None and right is not None:
                left_text = source_text_for_node(left, tree)
                right_text = source_text_for_node(right, tree)
                if left_text and right_text:
                    result.append((left_text.strip(), right_text.strip()))
                    continue
            expr = getattr(selector, "expr", None)
            if expr is not None:
                expr_text = source_text_for_node(expr, tree)
                if expr_text:
                    result.append(("0", expr_text.strip()))
                    continue
    return result


def declarator_unpacked_dimension_widths(raw: object, scope: object = None) -> list[int | None]:
    """Return [size, ...] element count for each unpacked dimension of the declarator."""
    dims = getattr(raw, "dimensions", None)
    if not dims:
        return []
    from ..syntax_queries import evaluate_constant_expression

    result: list[int | None] = []
    for dim in dims:
        spec = getattr(dim, "specifier", None)
        selector = getattr(spec, "selector", None)
        dim_w = None
        if selector is not None:
            left = getattr(selector, "left", None)
            right = getattr(selector, "right", None)
            if left is not None and right is not None:
                msb = evaluate_constant_expression(left, scope=scope)
                lsb = evaluate_constant_expression(right, scope=scope)
                if msb is not None and lsb is not None:
                    dim_w = abs(msb - lsb) + 1
            else:
                expr = getattr(selector, "expr", None)
                if expr is not None:
                    dim_w = evaluate_constant_expression(expr, scope=scope)
        result.append(dim_w)
    return result


def declarator_bit_width(ctx: "Context") -> int | None:
    dims = _declarator_owner_packed_dimensions(ctx)
    if dims:
        from ..syntax_queries import evaluate_constant_expression

        scope = getattr(ctx, "scope", lambda: None)()
        total_width = 1
        all_folded = True
        for dim in dims:
            spec = getattr(dim, "specifier", None)
            selector = getattr(spec, "selector", None)
            if selector is not None:
                left = getattr(selector, "left", None)
                right = getattr(selector, "right", None)
                if left is not None and right is not None:
                    msb = evaluate_constant_expression(left, scope=scope)
                    lsb = evaluate_constant_expression(right, scope=scope)
                    if msb is not None and lsb is not None:
                        total_width *= (abs(msb - lsb) + 1)
                        continue
            all_folded = False
            break
        if all_folded:
            return total_width
        return None

    # When there are no packed dimensions, determine scalar width directly from AST keyword
    for ancestor in reversed(ctx.stack):
        raw = ancestor.raw
        kind = getattr(raw, "kind", None)
        dt = None
        if kind in ANSI_PORT_KINDS or kind == PORT_DECLARATION_KIND:
            header = getattr(raw, "header", None)
            if header is not None:
                dt = getattr(header, "dataType", None)
        elif kind in DATA_DECLARATION_KINDS or kind in NET_DECLARATION_KINDS:
            dt = getattr(raw, "type", None)
        elif kind in PARAMETER_DECLARATION_KINDS:
            dt = getattr(raw, "type", None)

        if dt is not None:
            kw = getattr(getattr(dt, "keyword", None), "valueText", None)
            if kw in ("integer", "int"):
                return 32
            if kw in ("time", "longint"):
                return 64
            if kw in ("shortint",):
                return 16
            if kw in ("byte",):
                return 8
            if kw in ("logic", "bit", "reg", "wire") or getattr(dt, "kind", None) == IMPLICIT_TYPE_KIND:
                return 1
            break

    return None


def declarator_is_signed(ctx: "Context") -> bool | None:
    for ancestor in reversed(ctx.stack):
        raw = ancestor.raw
        kind = getattr(raw, "kind", None)
        dt = None
        if kind in ANSI_PORT_KINDS or kind == PORT_DECLARATION_KIND:
            header = getattr(raw, "header", None)
            if header is not None:
                dt = getattr(header, "dataType", None)
        elif kind in DATA_DECLARATION_KINDS or kind in NET_DECLARATION_KINDS:
            dt = getattr(raw, "type", None)
        elif kind in PARAMETER_DECLARATION_KINDS:
            dt = getattr(raw, "type", None)

        if dt is not None:
            signing_tok = getattr(dt, "signing", None)
            if signing_tok is not None:
                st = getattr(signing_tok, "valueText", "")
                if st == "signed":
                    return True
                if st == "unsigned":
                    return False
            kw = getattr(getattr(dt, "keyword", None), "valueText", None)
            if kw in ("integer", "int", "shortint", "longint", "byte"):
                return True
            if kw in ("time", "logic", "bit", "reg", "wire") or getattr(dt, "kind", None) == IMPLICIT_TYPE_KIND:
                return False
            break

    return None


def declarator_packed_range(ctx: "Context") -> tuple[int | None, int | None]:
    dims = _declarator_owner_packed_dimensions(ctx)
    if dims:
        from ..syntax_queries import evaluate_constant_expression

        dim = dims[0]
        spec = getattr(dim, "specifier", None)
        selector = getattr(spec, "selector", None)
        if selector is not None:
            left = getattr(selector, "left", None)
            right = getattr(selector, "right", None)
            if left is not None and right is not None:
                scope = getattr(ctx, "scope", lambda: None)()
                msb = evaluate_constant_expression(left, scope=scope)
                lsb = evaluate_constant_expression(right, scope=scope)
                if msb is not None and lsb is not None:
                    return msb, lsb
        return None, None

    # When there are no packed dimensions, a declared scalar signal has implicit range (0, 0)
    width = declarator_bit_width(ctx)
    if width == 1:
        return 0, 0
    return None, None


def clocking_declaration_signals(
    raw: object, tree: SyntaxTree | None = None
) -> list[tuple[str, bool, bool, dict[str, object] | None]]:
    """Extract (signal_name, is_input, is_output, location) for clocking declaration items."""
    results: list[tuple[str, bool, bool, dict[str, object] | None]] = []
    if getattr(raw, "kind", None) != CLOCKING_DECLARATION_KIND:
        return results

    for item in getattr(raw, "items", []):
        direction = getattr(item, "direction", None)
        if direction is None:
            continue
        input_tok = getattr(direction, "input", None)
        output_tok = getattr(direction, "output", None)
        input_kind_name = getattr(getattr(input_tok, "kind", None), "name", "")
        output_kind_name = getattr(getattr(output_tok, "kind", None), "name", "")

        is_input = input_kind_name in ("InputKeyword", "InOutKeyword")
        is_output = output_kind_name == "OutputKeyword" or input_kind_name == "InOutKeyword"

        for decl in getattr(item, "decls", []):
            val = getattr(decl, "value", None)
            name: str | None = None
            if val is not None and hasattr(val, "expr"):
                name = identifier_name(val.expr)
            elif hasattr(decl, "name") and hasattr(decl.name, "valueText"):
                name = decl.name.valueText
            if not name:
                continue
            loc = node_location(decl, tree) if tree is not None else None
            results.append((name, is_input, is_output, loc))

    return results
