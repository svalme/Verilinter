import pyslang as sl


def _syntax_kind(name: str) -> object | None:
    return getattr(sl.SyntaxKind, name, None)


ALWAYS_BLOCK_KIND = sl.SyntaxKind.AlwaysBlock
ALWAYS_COMB_BLOCK_KIND = sl.SyntaxKind.AlwaysCombBlock
ALWAYS_FF_BLOCK_KIND = _syntax_kind("AlwaysFFBlock") or sl.SyntaxKind.AlwaysFFBlock
ALWAYS_LATCH_BLOCK_KIND = sl.SyntaxKind.AlwaysLatchBlock
INITIAL_BLOCK_KIND = sl.SyntaxKind.InitialBlock
FINAL_BLOCK_KIND = sl.SyntaxKind.FinalBlock
CONTINUOUS_ASSIGN_KIND = sl.SyntaxKind.ContinuousAssign
CONDITIONAL_STATEMENT_KIND = _syntax_kind("ConditionalStatement")
CASE_STATEMENT_KIND = _syntax_kind("CaseStatement")
TIMING_CONTROL_STATEMENT_KIND = _syntax_kind("TimingControlStatement")
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
DISABLE_TOKEN_KIND = sl.TokenKind.DisableKeyword
EVENT_TRIGGER_TOKEN_KINDS = {
    sl.TokenKind.MinusArrow,
    sl.TokenKind.MinusDoubleArrow,
}
FOREVER_TOKEN_KIND = sl.TokenKind.ForeverKeyword
INSIDE_TOKEN_KIND = sl.TokenKind.InsideKeyword
WAIT_TOKEN_KIND = sl.TokenKind.WaitKeyword
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
    ALWAYS_FF_BLOCK_KIND,
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

UNIQUE0_TOKEN_KIND = getattr(sl.TokenKind, "Unique0Keyword", None)

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

WAND_WOR_TOKEN_KINDS = {
    kind
    for kind in (
        _syntax_kind("WAndKeyword"),
        _syntax_kind("WOrKeyword"),
        sl.TokenKind.WAndKeyword,
        sl.TokenKind.WOrKeyword,
    )
    if kind is not None
}

TRIREG_TOKEN_KIND = _syntax_kind("TriRegKeyword") or sl.TokenKind.TriRegKeyword

SUPPLY0_SUPPLY1_TOKEN_KINDS = {
    kind
    for kind in (
        _syntax_kind("Supply0Keyword"),
        _syntax_kind("Supply1Keyword"),
        sl.TokenKind.Supply0Keyword,
        sl.TokenKind.Supply1Keyword,
    )
    if kind is not None
}

TRAN_RTRAN_TOKEN_KINDS = {
    kind
    for kind in (
        _syntax_kind("TranKeyword"),
        _syntax_kind("RtranKeyword"),
        sl.TokenKind.TranKeyword,
        sl.TokenKind.RtranKeyword,
    )
    if kind is not None
}

TRANIF_RTRANIF_TOKEN_KINDS = {
    kind
    for kind in (
        _syntax_kind("TranIf0Keyword"),
        _syntax_kind("TranIf1Keyword"),
        _syntax_kind("RtranIf0Keyword"),
        _syntax_kind("RtranIf1Keyword"),
        sl.TokenKind.TranIf0Keyword,
        sl.TokenKind.TranIf1Keyword,
        sl.TokenKind.RtranIf0Keyword,
        sl.TokenKind.RtranIf1Keyword,
    )
    if kind is not None
}


PORT_DIRECTION_TOKEN_KINDS = {
    sl.TokenKind.InputKeyword: "input",
    sl.TokenKind.OutputKeyword: "output",
    sl.TokenKind.InOutKeyword: "inout",
    sl.TokenKind.RefKeyword: "ref",
}


__all__ = [
    "ALWAYS_BLOCK_KIND",
    "ALWAYS_COMB_BLOCK_KIND",
    "ALWAYS_FF_BLOCK_KIND",
    "ALWAYS_LATCH_BLOCK_KIND",
    "ASSIGNMENT_KINDS",
    "ASSIGN_DEASSIGN_TOKEN_KINDS",
    "BLOCK_STATEMENT_KINDS",
    "CASE_STATEMENT_KIND",
    "CASE_STYLE_TOKEN_KINDS",
    "CASE_TOKEN_KINDS",
    "CONDITIONAL_STATEMENT_KIND",
    "CONTINUOUS_ASSIGN_KIND",
    "DISABLE_TOKEN_KIND",
    "DEFPARAM_TOKEN_KIND",
    "ENDCASE_TOKEN_KIND",
    "EVENT_TRIGGER_TOKEN_KINDS",
    "FINAL_BLOCK_KIND",
    "FOREVER_TOKEN_KIND",
    "FORCE_RELEASE_TOKEN_KINDS",
    "INITIAL_BLOCK_KIND",
    "INSIDE_TOKEN_KIND",
    "PORT_DIRECTION_TOKEN_KINDS",
    "PROCEDURAL_BLOCK_KINDS",
    "READ_WRITE_ASSIGNMENT_KINDS",
    "READ_WRITE_UNARY_KINDS",
    "SIMPLE_ASSIGNMENT_KINDS",
    "SUPPLY0_SUPPLY1_TOKEN_KINDS",
    "TIMING_CONTROL_STATEMENT_KIND",
    "TRANIF_RTRANIF_TOKEN_KINDS",
    "TRAN_RTRAN_TOKEN_KINDS",
    "TRIREG_TOKEN_KIND",
    "UNIQUE0_TOKEN_KIND",
    "UNIQUE_PRIORITY_TOKEN_KINDS",
    "WAIT_TOKEN_KIND",
    "WAND_WOR_TOKEN_KINDS",
]
