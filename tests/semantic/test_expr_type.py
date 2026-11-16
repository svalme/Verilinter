from src.pkg.semantic.expr_type import ExprType, WidthDetermination


def test_equal_widths_do_not_differ() -> None:
    assert not ExprType(4, False).differs_from(4)


def test_a_narrower_self_determined_expression_differs() -> None:
    assert ExprType(4, False).differs_from(5)


def test_a_wider_self_determined_expression_differs() -> None:
    assert ExprType(8, False).differs_from(4)


def test_a_narrower_context_determined_expression_is_extended() -> None:
    assert not ExprType(4, False, WidthDetermination.CONTEXT).differs_from(5)


def test_a_wider_context_determined_expression_differs() -> None:
    assert ExprType(8, False, WidthDetermination.CONTEXT).differs_from(4)


def test_an_unknown_width_never_differs() -> None:
    assert not ExprType(None, None).differs_from(4)
    assert not ExprType(4, None).differs_from(None)
