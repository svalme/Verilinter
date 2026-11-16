from src.pkg.semantic.symbol import Symbol


def _symbol(bit_width: int | None, unpacked_widths: list[int | None]) -> Symbol:
    symbol = Symbol(name="s", kind="variable")
    symbol.bit_width = bit_width
    symbol.unpacked_dimension_widths = unpacked_widths
    return symbol


def test_a_plain_vector_is_its_own_whole_width() -> None:
    assert _symbol(8, []).whole_width == 8


def test_unpacked_dimensions_multiply_the_element_width() -> None:
    assert _symbol(32, [2, 10]).whole_width == 640


def test_an_unknown_unpacked_dimension_gives_no_whole_width() -> None:
    assert _symbol(32, [2, None]).whole_width is None


def test_an_unknown_element_width_gives_no_whole_width() -> None:
    assert _symbol(None, [4]).whole_width is None
