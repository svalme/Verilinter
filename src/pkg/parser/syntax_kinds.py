import pyslang as sl


def _syntax_kind(name: str) -> object | None:
    return getattr(sl.SyntaxKind, name, None)


def _token_kind(name: str) -> object | None:
    return getattr(sl.TokenKind, name, None)


ALWAYS_BLOCK_KIND = sl.SyntaxKind.AlwaysBlock
ALWAYS_COMB_BLOCK_KIND = sl.SyntaxKind.AlwaysCombBlock
ALWAYS_FF_BLOCK_KIND = _syntax_kind("AlwaysFFBlock") or sl.SyntaxKind.AlwaysFFBlock
ALWAYS_LATCH_BLOCK_KIND = sl.SyntaxKind.AlwaysLatchBlock
INITIAL_BLOCK_KIND = sl.SyntaxKind.InitialBlock
FINAL_BLOCK_KIND = sl.SyntaxKind.FinalBlock
CONTINUOUS_ASSIGN_KIND = sl.SyntaxKind.ContinuousAssign
GENERATE_BLOCK_KIND = sl.SyntaxKind.GenerateBlock
CLOCKING_DECLARATION_KIND = _syntax_kind("ClockingDeclaration")
CONDITIONAL_STATEMENT_KIND = _syntax_kind("ConditionalStatement")
CONDITIONAL_EXPRESSION_KIND = _syntax_kind("ConditionalExpression")
ELSE_CLAUSE_KIND = _syntax_kind("ElseClause")
MODULE_DECLARATION_KIND = _syntax_kind("ModuleDeclaration")
EVENT_TYPE_KIND = _syntax_kind("EventType")
COMPILATION_UNIT_KIND = _syntax_kind("CompilationUnit")
INTEGER_LITERAL_EXPRESSION_KIND = _syntax_kind("IntegerLiteralExpression")
INTEGER_VECTOR_EXPRESSION_KIND = _syntax_kind("IntegerVectorExpression")
REAL_LITERAL_EXPRESSION_KIND = _syntax_kind("RealLiteralExpression")
TIME_LITERAL_EXPRESSION_KIND = _syntax_kind("TimeLiteralExpression")
UNBASED_UNSIZED_LITERAL_EXPRESSION_KIND = _syntax_kind("UnbasedUnsizedLiteralExpression")
EQUALITY_EXPRESSION_KIND = _syntax_kind("EqualityExpression")
INEQUALITY_EXPRESSION_KIND = _syntax_kind("InequalityExpression")
GREATER_THAN_EXPRESSION_KIND = _syntax_kind("GreaterThanExpression")
GREATER_THAN_EQUAL_EXPRESSION_KIND = _syntax_kind("GreaterThanEqualExpression")
LESS_THAN_EXPRESSION_KIND = _syntax_kind("LessThanExpression")
LESS_THAN_EQUAL_EXPRESSION_KIND = _syntax_kind("LessThanEqualExpression")
CASE_EQUALITY_EXPRESSION_KIND = _syntax_kind("CaseEqualityExpression")
CASE_INEQUALITY_EXPRESSION_KIND = _syntax_kind("CaseInequalityExpression")
WILDCARD_EQUALITY_EXPRESSION_KIND = _syntax_kind("WildcardEqualityExpression")
WILDCARD_INEQUALITY_EXPRESSION_KIND = _syntax_kind("WildcardInequalityExpression")

COMPARISON_EXPRESSION_KINDS = {
    kind
    for kind in (
        EQUALITY_EXPRESSION_KIND,
        INEQUALITY_EXPRESSION_KIND,
        GREATER_THAN_EXPRESSION_KIND,
        GREATER_THAN_EQUAL_EXPRESSION_KIND,
        LESS_THAN_EXPRESSION_KIND,
        LESS_THAN_EQUAL_EXPRESSION_KIND,
        CASE_EQUALITY_EXPRESSION_KIND,
        CASE_INEQUALITY_EXPRESSION_KIND,
        WILDCARD_EQUALITY_EXPRESSION_KIND,
        WILDCARD_INEQUALITY_EXPRESSION_KIND,
    )
    if kind is not None
}
FOR_LOOP_STATEMENT_KIND = _syntax_kind("ForLoopStatement")
CASE_STATEMENT_KIND = _syntax_kind("CaseStatement")
STANDARD_CASE_ITEM_KIND = _syntax_kind("StandardCaseItem")
DEFAULT_CASE_ITEM_KIND = _syntax_kind("DefaultCaseItem")
PATTERN_CASE_ITEM_KIND = _syntax_kind("PatternCaseItem")
CASE_ITEM_KINDS = {
    kind
    for kind in (
        STANDARD_CASE_ITEM_KIND,
        DEFAULT_CASE_ITEM_KIND,
        PATTERN_CASE_ITEM_KIND,
    )
    if kind is not None
}
TIMESCALE_DIRECTIVE_KIND = _syntax_kind("TimeScaleDirective")
DEFAULT_NETTYPE_DIRECTIVE_KIND = _syntax_kind("DefaultNetTypeDirective")
CHECKER_DECLARATION_KIND = _syntax_kind("CheckerDeclaration")
DO_WHILE_STATEMENT_KIND = _syntax_kind("DoWhileStatement")
INTERFACE_DECLARATION_KIND = _syntax_kind("InterfaceDeclaration")
LOOP_GENERATE_KIND = _syntax_kind("LoopGenerate")
MODPORT_DECLARATION_KIND = _syntax_kind("ModportDeclaration")
PACKAGE_DECLARATION_KIND = _syntax_kind("PackageDeclaration")
PACKAGE_IMPORT_DECLARATION_KIND = _syntax_kind("PackageImportDeclaration")
PROGRAM_DECLARATION_KIND = _syntax_kind("ProgramDeclaration")
TASK_DECLARATION_KIND = _syntax_kind("TaskDeclaration")
TIMING_CONTROL_STATEMENT_KIND = _syntax_kind("TimingControlStatement")
EXPRESSION_STATEMENT_KIND = _syntax_kind("ExpressionStatement")
IF_GENERATE_KIND = _syntax_kind("IfGenerate")
SYSTEM_NAME_KIND = _syntax_kind("SystemName")
FUNCTION_PORT_KIND = _syntax_kind("FunctionPort")
ARGUMENT_LIST_KIND = _syntax_kind("ArgumentList")
ORDERED_ARGUMENT_KIND = _syntax_kind("OrderedArgument")
NAMED_ARGUMENT_KIND = _syntax_kind("NamedArgument")
NAMED_PORT_CONNECTION_KIND = _syntax_kind("NamedPortConnection")
ORDERED_PORT_CONNECTION_KIND = _syntax_kind("OrderedPortConnection")
WILDCARD_PORT_CONNECTION_KIND = _syntax_kind("WildcardPortConnection")
EMPTY_PORT_CONNECTION_KIND = _syntax_kind("EmptyPortConnection")
PORT_CONNECTION_KINDS = {
    kind
    for kind in (
        NAMED_PORT_CONNECTION_KIND,
        ORDERED_PORT_CONNECTION_KIND,
        WILDCARD_PORT_CONNECTION_KIND,
        EMPTY_PORT_CONNECTION_KIND,
    )
    if kind is not None
}
NAMED_PARAM_ASSIGNMENT_KIND = _syntax_kind("NamedParamAssignment")
ORDERED_PARAM_ASSIGNMENT_KIND = _syntax_kind("OrderedParamAssignment")
PARAM_ASSIGNMENT_KINDS = {
    kind
    for kind in (
        NAMED_PARAM_ASSIGNMENT_KIND,
        ORDERED_PARAM_ASSIGNMENT_KIND,
    )
    if kind is not None
}
CONDITIONAL_STATEMENT_KIND = _syntax_kind("ConditionalStatement")
ELSE_CLAUSE_KIND = _syntax_kind("ElseClause")
ASSIGNMENT_PATTERN_ITEM_KIND = _syntax_kind("AssignmentPatternItem")
IMPLICIT_ANSI_PORT_KIND = _syntax_kind("ImplicitAnsiPort")
EXPLICIT_ANSI_PORT_KIND = _syntax_kind("ExplicitAnsiPort")
ANSI_PORT_KINDS = {
    kind
    for kind in (
        IMPLICIT_ANSI_PORT_KIND,
        EXPLICIT_ANSI_PORT_KIND,
    )
    if kind is not None
}
PORT_DECLARATION_KIND = _syntax_kind("PortDeclaration")
ALL_PORT_DECLARATION_KINDS = {
    kind
    for kind in (
        IMPLICIT_ANSI_PORT_KIND,
        EXPLICIT_ANSI_PORT_KIND,
        PORT_DECLARATION_KIND,
        FUNCTION_PORT_KIND,
    )
    if kind is not None
}
DATA_DECLARATION_KIND = _syntax_kind("DataDeclaration")
CHECKER_DATA_DECLARATION_KIND = _syntax_kind("CheckerDataDeclaration")
DATA_DECLARATION_KINDS = {
    kind
    for kind in (
        DATA_DECLARATION_KIND,
        CHECKER_DATA_DECLARATION_KIND,
    )
    if kind is not None
}
NET_DECLARATION_KIND = _syntax_kind("NetDeclaration")
USER_DEFINED_NET_DECLARATION_KIND = _syntax_kind("UserDefinedNetDeclaration")
NET_DECLARATION_KINDS = {
    kind
    for kind in (
        NET_DECLARATION_KIND,
        USER_DEFINED_NET_DECLARATION_KIND,
    )
    if kind is not None
}
PARAMETER_DECLARATION_KIND = _syntax_kind("ParameterDeclaration")
PARAMETER_DECLARATION_STATEMENT_KIND = _syntax_kind("ParameterDeclarationStatement")
PARAMETER_DECLARATION_KINDS = {
    kind
    for kind in (
        PARAMETER_DECLARATION_KIND,
        PARAMETER_DECLARATION_STATEMENT_KIND,
    )
    if kind is not None
}
IMPLICIT_TYPE_KIND = _syntax_kind("ImplicitType")
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
EVENT_CONTROL_KINDS = {
    kind
    for kind in (
        _syntax_kind("EventControl"),
        _syntax_kind("EventControlWithExpression"),
        _syntax_kind("ImplicitEventControl"),
        _syntax_kind("RepeatedEventControl"),
    )
    if kind is not None
}
EVENT_EXPRESSION_KINDS = {
    kind
    for kind in (
        _syntax_kind("SignalEventExpression"),
        _syntax_kind("BinaryEventExpression"),
        _syntax_kind("ParenthesizedEventExpression"),
        _syntax_kind("BinaryBlockEventExpression"),
        _syntax_kind("PrimaryBlockEventExpression"),
    )
    if kind is not None
}
EVENT_CONTROL_OR_EXPRESSION_KINDS = EVENT_CONTROL_KINDS | EVENT_EXPRESSION_KINDS
UNARY_LOGICAL_NOT_EXPRESSION_KIND = _syntax_kind("UnaryLogicalNotExpression")
SIMPLE_PROPERTY_EXPR_KIND = _syntax_kind("SimplePropertyExpr")
SIMPLE_SEQUENCE_EXPR_KIND = _syntax_kind("SimpleSequenceExpr")
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
LOCALPARAM_TOKEN_KIND = sl.TokenKind.LocalParamKeyword
PARAMETER_TOKEN_KIND = sl.TokenKind.ParameterKeyword

NONBLOCKING_ASSIGNMENT_KIND = sl.SyntaxKind.NonblockingAssignmentExpression

SIMPLE_ASSIGNMENT_KINDS = {
    sl.SyntaxKind.AssignmentExpression,
    NONBLOCKING_ASSIGNMENT_KIND,
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

STAR_TOKEN_KIND = getattr(sl.TokenKind, "Star", None)
DOT_TOKEN_KIND = _token_kind("Dot")
CASE_KEYWORD_TOKEN_KIND = _token_kind("CaseKeyword")
CASEX_KEYWORD_TOKEN_KIND = _token_kind("CaseXKeyword")
CASEZ_KEYWORD_TOKEN_KIND = _token_kind("CaseZKeyword")
ENDCASE_KEYWORD_TOKEN_KIND = _token_kind("EndCaseKeyword")
POSEDGE_KEYWORD_TOKEN_KIND = _token_kind("PosEdgeKeyword")
NEGEDGE_KEYWORD_TOKEN_KIND = _token_kind("NegEdgeKeyword")
EQUALS_TOKEN_KIND = _token_kind("Equals")
LESS_THAN_EQUALS_TOKEN_KIND = _token_kind("LessThanEquals")
INOUT_KEYWORD_TOKEN_KIND = _token_kind("InOutKeyword")
UNIQUE_KEYWORD_TOKEN_KIND = _token_kind("UniqueKeyword")
PRIORITY_KEYWORD_TOKEN_KIND = _token_kind("PriorityKeyword")

# pyslang uses `ScopedNameSyntax` for BOTH `pkg::name` package scope resolution
# AND `struct_var.field` member access -- syntactically identical shape at parse
# time (before elaboration can tell a namespace path from a struct/interface
# member path), distinguishable only by `.separator.kind` (DoubleColon vs Dot).
# Any predicate that treats a `ScopedNameSyntax` segment as a package/namespace
# reference MUST check this, or it will misfire on ordinary `var.field` access.
DOUBLE_COLON_TOKEN_KIND = getattr(sl.TokenKind, "DoubleColon", None)

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

SWITCH_PRIMITIVE_TOKEN_KINDS = {
    kind
    for kind in (
        getattr(sl.TokenKind, name, None)
        for name in (
            "CmosKeyword",
            "RcmosKeyword",
            "NmosKeyword",
            "PmosKeyword",
            "RnmosKeyword",
            "RpmosKeyword",
            "PullUpKeyword",
            "PullDownKeyword",
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

LET_DECLARATION_KIND = _syntax_kind("LetDeclaration")
CONFIG_DECLARATION_KIND = _syntax_kind("ConfigDeclaration")
RANDSEQUENCE_STATEMENT_KIND = _syntax_kind("RandSequenceStatement")
EXPECT_RESTRICT_PROPERTY_KINDS = {
    kind
    for kind in (_syntax_kind("ExpectPropertyStatement"), _syntax_kind("RestrictPropertyStatement"))
    if kind is not None
}
VIRTUAL_INTERFACE_TYPE_KIND = _syntax_kind("VirtualInterfaceType")
DPI_IMPORT_EXPORT_KINDS = {
    kind
    for kind in (_syntax_kind("DPIImport"), _syntax_kind("DPIExport"))
    if kind is not None
}
REAL_TYPE_KINDS = {
    kind
    for kind in (_syntax_kind("RealType"), _syntax_kind("ShortRealType"), _syntax_kind("RealTimeType"))
    if kind is not None
}
STRING_TYPE_KIND = _syntax_kind("StringType")
CHANDLE_TYPE_KIND = _syntax_kind("CHandleType")

VARIABLE_DIMENSION_KIND = _syntax_kind("VariableDimension")
QUEUE_DIMENSION_SPECIFIER_KIND = _syntax_kind("QueueDimensionSpecifier")
WILDCARD_DIMENSION_SPECIFIER_KIND = _syntax_kind("WildcardDimensionSpecifier")
RANGE_DIMENSION_SPECIFIER_KIND = _syntax_kind("RangeDimensionSpecifier")

SHIFT_EXPRESSION_KINDS = {
    kind
    for kind in (
        _syntax_kind("LogicalShiftLeftExpression"),
        _syntax_kind("LogicalShiftRightExpression"),
        _syntax_kind("ArithmeticShiftLeftExpression"),
        _syntax_kind("ArithmeticShiftRightExpression"),
    )
    if kind is not None
}
DIVIDE_EXPRESSION_KIND = _syntax_kind("DivideExpression")
MOD_EXPRESSION_KIND = _syntax_kind("ModExpression")
ADD_SUBTRACT_EXPRESSION_KINDS = {
    kind
    for kind in (_syntax_kind("AddExpression"), _syntax_kind("SubtractExpression"))
    if kind is not None
}
MULTIPLY_EXPRESSION_KIND = _syntax_kind("MultiplyExpression")
UNARY_MINUS_EXPRESSION_KIND = _syntax_kind("UnaryMinusExpression")
PARENTHESIZED_EXPRESSION_KIND = _syntax_kind("ParenthesizedExpression")
EMPTY_STATEMENT_KIND = _syntax_kind("EmptyStatement")
BIT_SELECT_KIND = _syntax_kind("BitSelect")
ELEMENT_SELECT_KIND = _syntax_kind("ElementSelect")
SIMPLE_RANGE_SELECT_KIND = _syntax_kind("SimpleRangeSelect")
ASCENDING_RANGE_SELECT_KIND = _syntax_kind("AscendingRangeSelect")
DESCENDING_RANGE_SELECT_KIND = _syntax_kind("DescendingRangeSelect")
RANGE_SELECT_KINDS = {
    kind
    for kind in (
        SIMPLE_RANGE_SELECT_KIND,
        ASCENDING_RANGE_SELECT_KIND,
        DESCENDING_RANGE_SELECT_KIND,
    )
    if kind is not None
}
CONCATENATION_EXPRESSION_KIND = _syntax_kind("ConcatenationExpression")
MULTIPLE_CONCATENATION_EXPRESSION_KIND = _syntax_kind("MultipleConcatenationExpression")
IDENTIFIER_NAME_KIND = _syntax_kind("IdentifierName")
IDENTIFIER_SELECT_NAME_KIND = _syntax_kind("IdentifierSelectName")
ELEMENT_SELECT_EXPRESSION_KIND = _syntax_kind("ElementSelectExpression")
ADD_EXPRESSION_KIND = _syntax_kind("AddExpression")
SUBTRACT_EXPRESSION_KIND = _syntax_kind("SubtractExpression")
POWER_EXPRESSION_KIND = _syntax_kind("PowerExpression")
UNARY_PLUS_EXPRESSION_KIND = _syntax_kind("UnaryPlusExpression")
UNARY_BITWISE_NOT_EXPRESSION_KIND = _syntax_kind("UnaryBitwiseNotExpression")
LOGICAL_SHIFT_LEFT_EXPRESSION_KIND = _syntax_kind("LogicalShiftLeftExpression")
LOGICAL_SHIFT_RIGHT_EXPRESSION_KIND = _syntax_kind("LogicalShiftRightExpression")
ARITHMETIC_SHIFT_LEFT_EXPRESSION_KIND = _syntax_kind("ArithmeticShiftLeftExpression")
ARITHMETIC_SHIFT_RIGHT_EXPRESSION_KIND = _syntax_kind("ArithmeticShiftRightExpression")
BINARY_AND_EXPRESSION_KIND = _syntax_kind("BinaryAndExpression")
BINARY_OR_EXPRESSION_KIND = _syntax_kind("BinaryOrExpression")
BINARY_XOR_EXPRESSION_KIND = _syntax_kind("BinaryXorExpression")


__all__ = [
    "ADD_EXPRESSION_KIND",
    "ADD_SUBTRACT_EXPRESSION_KINDS",
    "ALIAS_STATEMENT_KIND",
    "ALWAYS_BLOCK_KIND",
    "ALWAYS_COMB_BLOCK_KIND",
    "ALWAYS_FF_BLOCK_KIND",
    "ALWAYS_LATCH_BLOCK_KIND",
    "ARITHMETIC_SHIFT_LEFT_EXPRESSION_KIND",
    "ARITHMETIC_SHIFT_RIGHT_EXPRESSION_KIND",
    "ALL_PORT_DECLARATION_KINDS",
    "ANSI_PORT_KINDS",
    "ASCENDING_RANGE_SELECT_KIND",
    "ASSIGNMENT_KINDS",
    "ASSIGN_DEASSIGN_TOKEN_KINDS",
    "ASSIGNMENT_PATTERN_ITEM_KIND",
    "BINARY_AND_EXPRESSION_KIND",
    "BINARY_OR_EXPRESSION_KIND",
    "BINARY_XOR_EXPRESSION_KIND",
    "BIND_DIRECTIVE_KIND",
    "BIT_SELECT_KIND",
    "BLOCK_STATEMENT_KINDS",
    "ARGUMENT_LIST_KIND",
    "CASEX_KEYWORD_TOKEN_KIND",
    "CASEZ_KEYWORD_TOKEN_KIND",
    "CASE_EQUALITY_EXPRESSION_KIND",
    "CASE_INEQUALITY_EXPRESSION_KIND",
    "CASE_ITEM_KINDS",
    "CASE_KEYWORD_TOKEN_KIND",
    "CASE_STATEMENT_KIND",
    "CASE_STYLE_TOKEN_KINDS",
    "CASE_TOKEN_KINDS",
    "CHANDLE_TYPE_KIND",
    "CHECKER_DECLARATION_KIND",
    "CLASS_DECLARATION_KIND",
    "CLOCKING_DECLARATION_KIND",
    "COMPARISON_EXPRESSION_KINDS",
    "COMPILATION_UNIT_KIND",
    "CONCATENATION_EXPRESSION_KIND",
    "CONCURRENT_ASSERTION_KINDS",
    "CONDITIONAL_EXPRESSION_KIND",
    "CONDITIONAL_STATEMENT_KIND",
    "CONFIG_DECLARATION_KIND",
    "CONTINUOUS_ASSIGN_KIND",
    "COVERGROUP_DECLARATION_KIND",
    "COVER_CROSS_KIND",
    "DATA_DECLARATION_KIND",
    "DATA_DECLARATION_KINDS",
    "DEFAULT_CASE_ITEM_KIND",
    "DEFAULT_NETTYPE_DIRECTIVE_KIND",
    "DELAY_CONTROL_KINDS",
    "DESCENDING_RANGE_SELECT_KIND",
    "DISABLE_IFF_KIND",
    "DISABLE_STATEMENT_KIND",
    "DISABLE_TOKEN_KIND",
    "DIVIDE_EXPRESSION_KIND",
    "DOT_TOKEN_KIND",
    "DOUBLE_COLON_TOKEN_KIND",
    "DO_TOKEN_KIND",
    "DO_WHILE_STATEMENT_KIND",
    "DEFPARAM_ASSIGNMENT_KIND",
    "DEFPARAM_TOKEN_KIND",
    "DPI_IMPORT_EXPORT_KINDS",
    "ELEMENT_SELECT_EXPRESSION_KIND",
    "ELEMENT_SELECT_KIND",
    "ELSE_CLAUSE_KIND",
    "EMPTY_PORT_CONNECTION_KIND",
    "EMPTY_STATEMENT_KIND",
    "ENDCASE_KEYWORD_TOKEN_KIND",
    "ENDCASE_TOKEN_KIND",
    "EQUALS_TOKEN_KIND",
    "EQUALITY_EXPRESSION_KIND",
    "EXPECT_RESTRICT_PROPERTY_KINDS",
    "EXPLICIT_ANSI_PORT_KIND",
    "EXPRESSION_STATEMENT_KIND",
    "EVENT_CONTROL_KINDS",
    "EVENT_EXPRESSION_KINDS",
    "EVENT_CONTROL_OR_EXPRESSION_KINDS",
    "EVENT_TRIGGER_STATEMENT_KINDS",
    "EVENT_TRIGGER_TOKEN_KINDS",
    "EXTENDS_CLAUSE_KIND",
    "FOR_LOOP_STATEMENT_KIND",
    "FOR_TOKEN_KIND",
    "FOREACH_TOKEN_KIND",
    "FINAL_BLOCK_KIND",
    "FOREVER_TOKEN_KIND",
    "FORCE_RELEASE_TOKEN_KINDS",
    "FUNCTION_DECLARATION_KIND",
    "FUNCTION_PORT_KIND",
    "FUNCTION_PROTOTYPE_KIND",
    "GATE_PRIMITIVE_TOKEN_KINDS",
    "GENERATE_BLOCK_KIND",
    "GREATER_THAN_EQUAL_EXPRESSION_KIND",
    "GREATER_THAN_EXPRESSION_KIND",
    "IDENTIFIER_NAME_KIND",
    "IDENTIFIER_SELECT_NAME_KIND",
    "IF_GENERATE_KIND",
    "IMMEDIATE_ASSERTION_KINDS",
    "IMPLICIT_ANSI_PORT_KIND",
    "IMPLICIT_TYPE_KIND",
    "INEQUALITY_EXPRESSION_KIND",
    "INITIAL_BLOCK_KIND",
    "INOUT_KEYWORD_TOKEN_KIND",
    "INTEGER_LITERAL_EXPRESSION_KIND",
    "INTEGER_VECTOR_EXPRESSION_KIND",
    "INTERFACE_DECLARATION_KIND",
    "INSIDE_TOKEN_KIND",
    "INVOCATION_EXPRESSION_KIND",
    "LESS_THAN_EQUALS_TOKEN_KIND",
    "LESS_THAN_EQUAL_EXPRESSION_KIND",
    "LESS_THAN_EXPRESSION_KIND",
    "LET_DECLARATION_KIND",
    "LOGICAL_SHIFT_LEFT_EXPRESSION_KIND",
    "LOGICAL_SHIFT_RIGHT_EXPRESSION_KIND",
    "LOOP_GENERATE_KIND",
    "MODPORT_DECLARATION_KIND",
    "MODULE_DECLARATION_KIND",
    "MOD_EXPRESSION_KIND",
    "MULTIPLE_CONCATENATION_EXPRESSION_KIND",
    "MULTIPLY_EXPRESSION_KIND",
    "NAMED_ARGUMENT_KIND",
    "NAMED_PARAM_ASSIGNMENT_KIND",
    "NAMED_PORT_CONNECTION_KIND",
    "NAMED_TYPE_KIND",
    "NET_DECLARATION_KIND",
    "NET_DECLARATION_KINDS",
    "NONBLOCKING_ASSIGNMENT_KIND",
    "NEGEDGE_KEYWORD_TOKEN_KIND",
    "ORDERED_ARGUMENT_KIND",
    "ORDERED_PARAM_ASSIGNMENT_KIND",
    "ORDERED_PORT_CONNECTION_KIND",
    "PACKAGE_DECLARATION_KIND",
    "PACKAGE_IMPORT_DECLARATION_KIND",
    "PARALLEL_BLOCK_STATEMENT_KIND",
    "PARAMETER_DECLARATION_KIND",
    "PARAMETER_DECLARATION_KINDS",
    "PARAMETER_DECLARATION_STATEMENT_KIND",
    "PARAM_ASSIGNMENT_KINDS",
    "PARENTHESIZED_EXPRESSION_KIND",
    "PATTERN_CASE_ITEM_KIND",
    "PORT_CONNECTION_KINDS",
    "PORT_DECLARATION_KIND",
    "PORT_DIRECTION_TOKEN_KINDS",
    "POSEDGE_KEYWORD_TOKEN_KIND",
    "POWER_EXPRESSION_KIND",
    "PRIORITY_KEYWORD_TOKEN_KIND",
    "PRIMITIVE_DECLARATION_KIND",
    "PRIMITIVE_INSTANTIATION_KIND",
    "PROGRAM_DECLARATION_KIND",
    "PROCEDURAL_BLOCK_KINDS",
    "PROPERTY_DECLARATION_KIND",
    "QUEUE_DIMENSION_SPECIFIER_KIND",
    "RANDSEQUENCE_STATEMENT_KIND",
    "RANGE_DIMENSION_SPECIFIER_KIND",
    "RANGE_SELECT_KINDS",
    "READ_WRITE_ASSIGNMENT_KINDS",
    "READ_WRITE_UNARY_KINDS",
    "REAL_LITERAL_EXPRESSION_KIND",
    "REAL_TYPE_KINDS",
    "REPEAT_TOKEN_KIND",
    "SCOPED_NAME_KIND",
    "SEQUENCE_DECLARATION_KIND",
    "SHIFT_EXPRESSION_KINDS",
    "SIMPLE_ASSIGNMENT_KINDS",
    "SIMPLE_PROPERTY_EXPR_KIND",
    "SIMPLE_RANGE_SELECT_KIND",
    "SIMPLE_SEQUENCE_EXPR_KIND",
    "SPECIFY_BLOCK_KIND",
    "STANDARD_CASE_ITEM_KIND",
    "STAR_TOKEN_KIND",
    "STRING_TYPE_KIND",
    "SUBTRACT_EXPRESSION_KIND",
    "SYSTEM_NAME_KIND",
    "TASK_DECLARATION_KIND",
    "SUPPLY0_SUPPLY1_TOKEN_KINDS",
    "SWITCH_PRIMITIVE_TOKEN_KINDS",
    "TIME_LITERAL_EXPRESSION_KIND",
    "TIMESCALE_DIRECTIVE_KIND",
    "TIMING_CONTROL_STATEMENT_KIND",
    "TRANIF_RTRANIF_TOKEN_KINDS",
    "TRAN_RTRAN_TOKEN_KINDS",
    "TRIREG_TOKEN_KIND",
    "UNARY_BITWISE_NOT_EXPRESSION_KIND",
    "UNARY_LOGICAL_NOT_EXPRESSION_KIND",
    "UNARY_MINUS_EXPRESSION_KIND",
    "UNARY_PLUS_EXPRESSION_KIND",
    "UNBASED_UNSIZED_LITERAL_EXPRESSION_KIND",
    "UNIQUE0_TOKEN_KIND",
    "UNIQUE_KEYWORD_TOKEN_KIND",
    "UNIQUE_PRIORITY_TOKEN_KINDS",
    "UWIRE_TOKEN_KIND",
    "VARIABLE_DIMENSION_KIND",
    "VIRTUAL_INTERFACE_TYPE_KIND",
    "WAIT_TOKEN_KIND",
    "WHILE_TOKEN_KIND",
    "WAND_WOR_TOKEN_KINDS",
    "WILDCARD_DIMENSION_SPECIFIER_KIND",
    "WILDCARD_EQUALITY_EXPRESSION_KIND",
    "WILDCARD_INEQUALITY_EXPRESSION_KIND",
    "WILDCARD_PORT_CONNECTION_KIND",
]
