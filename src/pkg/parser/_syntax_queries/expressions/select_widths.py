"""The width of a bit-select, part-select or element select of a declared symbol."""
from __future__ import annotations

from ..shapes import element_select_index_or_range
from .constant_evaluation import evaluate_constant_expression, evaluate_constant_text_expression


def _selector_width(selector: object, scope: object = None) -> int | None:
    """Return the bit-width selected by an `ElementSelectSyntax` node."""
    unwrapped = element_select_index_or_range(selector)
    if unwrapped is None:
        return None
    shape, payload = unwrapped
    if shape == "bit":
        return 1
    if shape == "simple_range":
        left, right = payload
        l_val = evaluate_constant_expression(left, scope=scope)
        r_val = evaluate_constant_expression(right, scope=scope)
        if l_val is not None and r_val is not None:
            return abs(l_val - r_val) + 1
        return None
    if shape in ("ascending", "descending"):
        _base, width_expr = payload
        return evaluate_constant_expression(width_expr, scope=scope)
    return None


def compute_sliced_width(
    symbol: object | None,
    selectors: list[object],
    scope: object = None,
) -> int | None:
    """Compute the bit width resulting from indexing or slicing an identifier with `selectors`.

    Supports:
    - Single-element bit selects on 1D vectors (`vec[i]` -> 1 bit)
    - Element selects on multi-dimensional packed arrays (`arr[i]` -> element slice width)
    - Nested element selects (`arr[i][j]` -> scalar bit width or sub-slice width)
    - Simple range selects (`vec[7:0]` -> 8 bits, `arr[3:1]` -> range count * inner element width)
    - Indexed part-selects (`vec[i +: 8]` -> 8 bits)
    """
    if not selectors:
        return getattr(symbol, "bit_width", None) if symbol is not None else None

    # Recover individual unpacked and packed dimension widths
    unpacked_widths: list[int | None] = []
    packed_widths: list[int | None] = []
    if symbol is not None:
        unpacked_widths = list(getattr(symbol, "unpacked_dimension_widths", []))
        if not unpacked_widths and getattr(symbol, "unpacked_dimensions", None):
            for msb_txt, lsb_txt in symbol.unpacked_dimensions:
                m = None
                l = None
                try:
                    m = int(msb_txt)
                except (ValueError, TypeError):
                    m = evaluate_constant_text_expression(msb_txt, scope=scope)
                try:
                    l = int(lsb_txt)
                except (ValueError, TypeError):
                    l = evaluate_constant_text_expression(lsb_txt, scope=scope)
                if isinstance(m, int) and isinstance(l, int):
                    unpacked_widths.append(abs(m - l) + 1)
                else:
                    unpacked_widths.append(None)

        packed_widths = list(getattr(symbol, "packed_dimension_widths", []))
        if not packed_widths and getattr(symbol, "packed_dimensions", None):
            for msb_txt, lsb_txt in symbol.packed_dimensions:
                m = None
                l = None
                try:
                    m = int(msb_txt)
                except (ValueError, TypeError):
                    m = evaluate_constant_text_expression(msb_txt, scope=scope)
                try:
                    l = int(lsb_txt)
                except (ValueError, TypeError):
                    l = evaluate_constant_text_expression(lsb_txt, scope=scope)
                if isinstance(m, int) and isinstance(l, int):
                    packed_widths.append(abs(m - l) + 1)
                else:
                    packed_widths.append(None)

        # If symbol has a known bit width and no explicit packed dimensions (e.g. 1-bit logic or multi-bit integer),
        # treat its packed element width as [symbol.bit_width] when unpacked dimensions exist.
        if unpacked_widths and not packed_widths and isinstance(getattr(symbol, "bit_width", None), int):
            packed_widths = [symbol.bit_width]

        # An element of a named type has the width of that type, which is not known here, and the
        # dimensions written after the type name are not recorded.
        named_dimensions = getattr(symbol, "named_type_dimension_count", None)
        if named_dimensions:
            return None
        if named_dimensions == 0:
            packed_widths = [*packed_widths, None]

    num_unpacked = len(unpacked_widths)

    # Compute single packed element bit width (product of all packed dimensions)
    packed_elem_width: int | None = None
    if packed_widths:
        if any(d is None for d in packed_widths):
            packed_elem_width = None
        else:
            prod = 1
            for d in packed_widths:
                prod *= d
            packed_elem_width = prod
    elif symbol is not None and isinstance(getattr(symbol, "bit_width", None), int):
        packed_elem_width = symbol.bit_width
    elif not unpacked_widths:
        packed_elem_width = None
    else:
        packed_elem_width = 1

    slice_width: int | None = None

    for s_idx, selector in enumerate(selectors):
        unwrapped = element_select_index_or_range(selector)
        if unwrapped is None:
            return None
        shape, payload = unwrapped
        is_last = (s_idx == len(selectors) - 1)

        if s_idx < num_unpacked:
            # Indexing or slicing an unpacked array dimension
            if shape == "bit":
                if is_last:
                    rem_unpacked = unpacked_widths[s_idx + 1:]
                    if any(d is None for d in rem_unpacked) or packed_elem_width is None:
                        slice_width = None
                    else:
                        prod = packed_elem_width
                        for d in rem_unpacked:
                            prod *= d
                        slice_width = prod
            elif shape == "simple_range":
                left, right = payload
                l_val = evaluate_constant_expression(left, scope=scope)
                r_val = evaluate_constant_expression(right, scope=scope)
                if l_val is None or r_val is None:
                    return None
                range_count = abs(l_val - r_val) + 1
                if is_last:
                    rem_unpacked = unpacked_widths[s_idx + 1:]
                    if any(d is None for d in rem_unpacked) or packed_elem_width is None:
                        slice_width = None
                    else:
                        prod = range_count * packed_elem_width
                        for d in rem_unpacked:
                            prod *= d
                        slice_width = prod
            elif shape in ("ascending", "descending"):
                _base, width_expr = payload
                w_val = evaluate_constant_expression(width_expr, scope=scope)
                if w_val is None:
                    return None
                if is_last:
                    rem_unpacked = unpacked_widths[s_idx + 1:]
                    if any(d is None for d in rem_unpacked) or packed_elem_width is None:
                        slice_width = None
                    else:
                        prod = w_val * packed_elem_width
                        for d in rem_unpacked:
                            prod *= d
                        slice_width = prod
        else:
            # Indexing or slicing packed dimensions
            p_idx = s_idx - num_unpacked

            if shape == "bit":
                if is_last:
                    rem_dims = packed_widths[p_idx + 1:] if packed_widths else []
                    if not rem_dims:
                        slice_width = 1
                    elif any(d is None for d in rem_dims):
                        slice_width = None
                    else:
                        prod = 1
                        for d in rem_dims:
                            prod *= d
                        slice_width = prod

            elif shape == "simple_range":
                left, right = payload
                l_val = evaluate_constant_expression(left, scope=scope)
                r_val = evaluate_constant_expression(right, scope=scope)
                if l_val is None or r_val is None:
                    return None
                range_count = abs(l_val - r_val) + 1
                if is_last:
                    rem_dims = packed_widths[p_idx + 1:] if packed_widths else []
                    if not rem_dims:
                        slice_width = range_count
                    elif any(d is None for d in rem_dims):
                        slice_width = None
                    else:
                        prod = range_count
                        for d in rem_dims:
                            prod *= d
                        slice_width = prod

            elif shape in ("ascending", "descending"):
                _base, width_expr = payload
                w_val = evaluate_constant_expression(width_expr, scope=scope)
                if w_val is None:
                    return None
                if is_last:
                    rem_dims = packed_widths[p_idx + 1:] if packed_widths else []
                    if not rem_dims:
                        slice_width = w_val
                    elif any(d is None for d in rem_dims):
                        slice_width = None
                    else:
                        prod = w_val
                        for d in rem_dims:
                            prod *= d
                        slice_width = prod

    return slice_width
