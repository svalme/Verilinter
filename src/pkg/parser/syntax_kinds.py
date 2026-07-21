import pyslang as sl


def _syntax_kind(name: str) -> object | None:
    return getattr(sl.SyntaxKind, name, None)


ALWAYS_BLOCK_KIND = sl.SyntaxKind.AlwaysBlock
ALWAYS_COMB_BLOCK_KIND = sl.SyntaxKind.AlwaysCombBlock
ALWAYS_LATCH_BLOCK_KIND = sl.SyntaxKind.AlwaysLatchBlock
INITIAL_BLOCK_KIND = sl.SyntaxKind.InitialBlock
FINAL_BLOCK_KIND = sl.SyntaxKind.FinalBlock
CONDITIONAL_STATEMENT_KIND = _syntax_kind("ConditionalStatement")
BLOCK_STATEMENT_KINDS = {
    kind
    for kind in (
        _syntax_kind("BlockStatement"),
        _syntax_kind("SequentialBlockStatement"),
        _syntax_kind("ParallelBlockStatement"),
    )
    if kind is not None
}
ENDCASE_TOKEN_KIND = sl.TokenKind.EndCaseKeyword
CASE_TOKEN_KINDS = {
    sl.TokenKind.CaseKeyword,
    sl.TokenKind.CaseXKeyword,
    sl.TokenKind.CaseZKeyword,
}

SIMPLE_ASSIGNMENT_KINDS = {
    sl.SyntaxKind.AssignmentExpression,
    sl.SyntaxKind.NonblockingAssignmentExpression,
}

READ_WRITE_ASSIGNMENT_KINDS = {
    kind
    for kind in (
        _syntax_kind("AddAssignmentExpression"),
        _syntax_kind("SubAssignmentExpression"),
        _syntax_kind("MulAssignmentExpression"),
        _syntax_kind("DivAssignmentExpression"),
        _syntax_kind("ModAssignmentExpression"),
        _syntax_kind("AndAssignmentExpression"),
        _syntax_kind("OrAssignmentExpression"),
        _syntax_kind("XorAssignmentExpression"),
        _syntax_kind("LogicalShiftLeftAssignmentExpression"),
        _syntax_kind("LogicalShiftRightAssignmentExpression"),
        _syntax_kind("ArithmeticShiftLeftAssignmentExpression"),
        _syntax_kind("ArithmeticShiftRightAssignmentExpression"),
    )
    if kind is not None
}

READ_WRITE_UNARY_KINDS = {
    kind
    for kind in (
        _syntax_kind("UnaryPreincrementExpression"),
        _syntax_kind("UnaryPredecrementExpression"),
        _syntax_kind("PostincrementExpression"),
        _syntax_kind("PostdecrementExpression"),
    )
    if kind is not None
}

ASSIGNMENT_KINDS = SIMPLE_ASSIGNMENT_KINDS | READ_WRITE_ASSIGNMENT_KINDS

PROCEDURAL_BLOCK_KINDS = {
    ALWAYS_BLOCK_KIND,
    ALWAYS_COMB_BLOCK_KIND,
    ALWAYS_LATCH_BLOCK_KIND,
    INITIAL_BLOCK_KIND,
    FINAL_BLOCK_KIND,
}

CASE_STYLE_TOKEN_KINDS = {
    sl.TokenKind.CaseXKeyword,
    sl.TokenKind.CaseZKeyword,
}

UNIQUE_PRIORITY_TOKEN_KINDS = {
    sl.TokenKind.UniqueKeyword,
    sl.TokenKind.PriorityKeyword,
}

DEFPARAM_TOKEN_KIND = _syntax_kind("DefParamKeyword") or sl.TokenKind.DefParamKeyword

FORCE_RELEASE_TOKEN_KINDS = {
    kind
    for kind in (
        _syntax_kind("ForceKeyword"),
        _syntax_kind("ReleaseKeyword"),
        sl.TokenKind.ForceKeyword,
        sl.TokenKind.ReleaseKeyword,
    )
    if kind is not None
}

ASSIGN_DEASSIGN_TOKEN_KINDS = {
    kind
    for kind in (
        _syntax_kind("AssignKeyword"),
        _syntax_kind("DeassignKeyword"),
        sl.TokenKind.AssignKeyword,
        sl.TokenKind.DeassignKeyword,
    )
    if kind is not None
}


__all__ = [
    "ALWAYS_BLOCK_KIND",
    "ALWAYS_COMB_BLOCK_KIND",
    "ALWAYS_LATCH_BLOCK_KIND",
    "ASSIGNMENT_KINDS",
    "ASSIGN_DEASSIGN_TOKEN_KINDS",
    "BLOCK_STATEMENT_KINDS",
    "CASE_STYLE_TOKEN_KINDS",
    "CASE_TOKEN_KINDS",
    "CONDITIONAL_STATEMENT_KIND",
    "DEFPARAM_TOKEN_KIND",
    "ENDCASE_TOKEN_KIND",
    "FINAL_BLOCK_KIND",
    "FORCE_RELEASE_TOKEN_KINDS",
    "INITIAL_BLOCK_KIND",
    "PROCEDURAL_BLOCK_KINDS",
    "READ_WRITE_ASSIGNMENT_KINDS",
    "READ_WRITE_UNARY_KINDS",
    "SIMPLE_ASSIGNMENT_KINDS",
    "UNIQUE_PRIORITY_TOKEN_KINDS",
]
