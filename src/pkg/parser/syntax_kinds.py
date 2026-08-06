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
CLOCKING_DECLARATION_KIND = _syntax_kind("ClockingDeclaration")
CONDITIONAL_STATEMENT_KIND = _syntax_kind("ConditionalStatement")
CASE_STATEMENT_KIND = _syntax_kind("CaseStatement")
CHECKER_DECLARATION_KIND = _syntax_kind("CheckerDeclaration")
DO_WHILE_STATEMENT_KIND = _syntax_kind("DoWhileStatement")
INTERFACE_DECLARATION_KIND = _syntax_kind("InterfaceDeclaration")
LOOP_GENERATE_KIND = _syntax_kind("LoopGenerate")
MODPORT_DECLARATION_KIND = _syntax_kind("ModportDeclaration")
PACKAGE_DECLARATION_KIND = _syntax_kind("PackageDeclaration")
PROGRAM_DECLARATION_KIND = _syntax_kind("ProgramDeclaration")
TASK_DECLARATION_KIND = _syntax_kind("TaskDeclaration")
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
PARALLEL_BLOCK_STATEMENT_KIND = _syntax_kind("ParallelBlockStatement")
ENDCASE_TOKEN_KIND = sl.TokenKind.EndCaseKeyword
DISABLE_TOKEN_KIND = sl.TokenKind.DisableKeyword
DO_TOKEN_KIND = sl.TokenKind.DoKeyword
EVENT_TRIGGER_TOKEN_KINDS = {
    sl.TokenKind.MinusArrow,
    sl.TokenKind.MinusDoubleArrow,
}
FOR_TOKEN_KIND = sl.TokenKind.ForKeyword
FOREACH_TOKEN_KIND = sl.TokenKind.ForeachKeyword
FOREVER_TOKEN_KIND = sl.TokenKind.ForeverKeyword
INSIDE_TOKEN_KIND = sl.TokenKind.InsideKeyword
REPEAT_TOKEN_KIND = sl.TokenKind.RepeatKeyword
WAIT_TOKEN_KIND = sl.TokenKind.WaitKeyword
WHILE_TOKEN_KIND = sl.TokenKind.WhileKeyword
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

SPECIFY_BLOCK_KIND = _syntax_kind("SpecifyBlock")
PRIMITIVE_DECLARATION_KIND = _syntax_kind("UdpDeclaration")
ALIAS_STATEMENT_KIND = _syntax_kind("NetAlias")
BIND_DIRECTIVE_KIND = _syntax_kind("BindDirective")

GATE_PRIMITIVE_TOKEN_KINDS = {
    kind
    for kind in (
        getattr(sl.TokenKind, name, None)
        for name in (
            "AndKeyword",
            "OrKeyword",
            "NandKeyword",
            "NorKeyword",
            "XorKeyword",
            "XnorKeyword",
            "NotKeyword",
            "BufKeyword",
            "BufIf0Keyword",
            "BufIf1Keyword",
            "NotIf0Keyword",
            "NotIf1Keyword",
        )
    )
    if kind is not None
}

DELAY_CONTROL_KINDS = {
    kind
    for kind in (_syntax_kind("DelayControl"), _syntax_kind("Delay3"))
    if kind is not None
}

IMMEDIATE_ASSERTION_KINDS = {
    kind
    for kind in (
        _syntax_kind("ImmediateAssertStatement"),
        _syntax_kind("ImmediateAssumeStatement"),
        _syntax_kind("ImmediateCoverStatement"),
    )
    if kind is not None
}

CONCURRENT_ASSERTION_KINDS = {
    kind
    for kind in (
        _syntax_kind("AssertPropertyStatement"),
        _syntax_kind("AssumePropertyStatement"),
        _syntax_kind("CoverPropertyStatement"),
    )
    if kind is not None
}

CLASS_DECLARATION_KIND = _syntax_kind("ClassDeclaration")
COVERGROUP_DECLARATION_KIND = _syntax_kind("CovergroupDeclaration")
SEQUENCE_DECLARATION_KIND = _syntax_kind("SequenceDeclaration")
PROPERTY_DECLARATION_KIND = _syntax_kind("PropertyDeclaration")
FUNCTION_DECLARATION_KIND = _syntax_kind("FunctionDeclaration")
FUNCTION_PROTOTYPE_KIND = _syntax_kind("FunctionPrototype")
PRIMITIVE_INSTANTIATION_KIND = _syntax_kind("PrimitiveInstantiation")
SCOPED_NAME_KIND = _syntax_kind("ScopedName")
DEFPARAM_ASSIGNMENT_KIND = _syntax_kind("DefParamAssignment")
DISABLE_STATEMENT_KIND = _syntax_kind("DisableStatement")
DISABLE_IFF_KIND = _syntax_kind("DisableIff")
NAMED_TYPE_KIND = _syntax_kind("NamedType")
INVOCATION_EXPRESSION_KIND = _syntax_kind("InvocationExpression")
COVER_CROSS_KIND = _syntax_kind("CoverCross")
EXTENDS_CLAUSE_KIND = _syntax_kind("ExtendsClause")
EVENT_TRIGGER_STATEMENT_KINDS = {
    kind
    for kind in (_syntax_kind("BlockingEventTriggerStatement"), _syntax_kind("NonblockingEventTriggerStatement"))
    if kind is not None
}

UWIRE_TOKEN_KIND = getattr(sl.TokenKind, "UWireKeyword", None)


__all__ = [
    "ALIAS_STATEMENT_KIND",
    "ALWAYS_BLOCK_KIND",
    "ALWAYS_COMB_BLOCK_KIND",
    "ALWAYS_FF_BLOCK_KIND",
    "ALWAYS_LATCH_BLOCK_KIND",
    "ASSIGNMENT_KINDS",
    "ASSIGN_DEASSIGN_TOKEN_KINDS",
    "BIND_DIRECTIVE_KIND",
    "BLOCK_STATEMENT_KINDS",
    "CASE_STATEMENT_KIND",
    "CASE_STYLE_TOKEN_KINDS",
    "CASE_TOKEN_KINDS",
    "CHECKER_DECLARATION_KIND",
    "CLASS_DECLARATION_KIND",
    "CLOCKING_DECLARATION_KIND",
    "CONCURRENT_ASSERTION_KINDS",
    "CONDITIONAL_STATEMENT_KIND",
    "CONTINUOUS_ASSIGN_KIND",
    "COVERGROUP_DECLARATION_KIND",
    "COVER_CROSS_KIND",
    "DELAY_CONTROL_KINDS",
    "DISABLE_IFF_KIND",
    "DISABLE_STATEMENT_KIND",
    "DISABLE_TOKEN_KIND",
    "DO_TOKEN_KIND",
    "DO_WHILE_STATEMENT_KIND",
    "DEFPARAM_ASSIGNMENT_KIND",
    "DEFPARAM_TOKEN_KIND",
    "ENDCASE_TOKEN_KIND",
    "EVENT_TRIGGER_STATEMENT_KINDS",
    "EVENT_TRIGGER_TOKEN_KINDS",
    "EXTENDS_CLAUSE_KIND",
    "FOR_TOKEN_KIND",
    "FOREACH_TOKEN_KIND",
    "FINAL_BLOCK_KIND",
    "FOREVER_TOKEN_KIND",
    "FORCE_RELEASE_TOKEN_KINDS",
    "FUNCTION_DECLARATION_KIND",
    "FUNCTION_PROTOTYPE_KIND",
    "GATE_PRIMITIVE_TOKEN_KINDS",
    "IMMEDIATE_ASSERTION_KINDS",
    "INITIAL_BLOCK_KIND",
    "INTERFACE_DECLARATION_KIND",
    "INSIDE_TOKEN_KIND",
    "INVOCATION_EXPRESSION_KIND",
    "LOOP_GENERATE_KIND",
    "MODPORT_DECLARATION_KIND",
    "NAMED_TYPE_KIND",
    "PACKAGE_DECLARATION_KIND",
    "PARALLEL_BLOCK_STATEMENT_KIND",
    "PORT_DIRECTION_TOKEN_KINDS",
    "PRIMITIVE_DECLARATION_KIND",
    "PRIMITIVE_INSTANTIATION_KIND",
    "PROGRAM_DECLARATION_KIND",
    "PROCEDURAL_BLOCK_KINDS",
    "PROPERTY_DECLARATION_KIND",
    "READ_WRITE_ASSIGNMENT_KINDS",
    "READ_WRITE_UNARY_KINDS",
    "REPEAT_TOKEN_KIND",
    "SCOPED_NAME_KIND",
    "SEQUENCE_DECLARATION_KIND",
    "SIMPLE_ASSIGNMENT_KINDS",
    "SPECIFY_BLOCK_KIND",
    "TASK_DECLARATION_KIND",
    "SUPPLY0_SUPPLY1_TOKEN_KINDS",
    "TIMING_CONTROL_STATEMENT_KIND",
    "TRANIF_RTRANIF_TOKEN_KINDS",
    "TRAN_RTRAN_TOKEN_KINDS",
    "TRIREG_TOKEN_KIND",
    "UNIQUE0_TOKEN_KIND",
    "UNIQUE_PRIORITY_TOKEN_KINDS",
    "UWIRE_TOKEN_KIND",
    "WAIT_TOKEN_KIND",
    "WHILE_TOKEN_KIND",
    "WAND_WOR_TOKEN_KINDS",
]
