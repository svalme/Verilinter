"""Raw parser-backed type aliases used outside `pkg.parser.syntax*`.

Keep this module narrowly about naming the parser classes we register against or
type against directly. Tree-shape questions such as "is this identifier-like?"
belong in parser helpers instead of being reimplemented at call sites.
"""

import pyslang as sl
from typing import TypeAlias


SyntaxTree: TypeAlias = sl.SyntaxTree
SyntaxNode: TypeAlias = sl.SyntaxNode
Token: TypeAlias = sl.Token
RawNode: TypeAlias = SyntaxNode | Token

ModuleDeclarationNode: TypeAlias = sl.ModuleDeclarationSyntax
DeclaratorNode: TypeAlias = sl.DeclaratorSyntax
PackageImportDeclarationNode: TypeAlias = sl.PackageImportDeclarationSyntax
# pyslang represents both `function` and `task` declarations with this same
# wrapper class, distinguishable only by `.kind` -- same shape as
# ModuleDeclarationNode covering module/package/interface/program.
FunctionDeclarationNode: TypeAlias = sl.FunctionDeclarationSyntax
ForLoopStatementNode: TypeAlias = sl.ForLoopStatementSyntax
ForeverStatementNode: TypeAlias = sl.ForeverStatementSyntax
LoopStatementNode: TypeAlias = sl.LoopStatementSyntax
DoWhileStatementNode: TypeAlias = sl.DoWhileStatementSyntax
JumpStatementNode: TypeAlias = sl.JumpStatementSyntax
ReturnStatementNode: TypeAlias = sl.ReturnStatementSyntax
WaitStatementNode: TypeAlias = sl.WaitStatementSyntax
RangeSelectNode: TypeAlias = sl.RangeSelectSyntax
StructUnionTypeNode: TypeAlias = sl.StructUnionTypeSyntax
LoopGenerateNode: TypeAlias = sl.LoopGenerateSyntax
TypedefDeclarationNode: TypeAlias = sl.TypedefDeclarationSyntax
ForwardTypedefDeclarationNode: TypeAlias = sl.ForwardTypedefDeclarationSyntax

IdentifierNameNode: TypeAlias = sl.IdentifierNameSyntax
IdentifierSelectNameNode: TypeAlias = sl.IdentifierSelectNameSyntax
IDENTIFIER_NAME_NODE_TYPES: tuple[type[SyntaxNode], ...] = (
    IdentifierNameNode,
    IdentifierSelectNameNode,
)

ProceduralBlockNode: TypeAlias = sl.ProceduralBlockSyntax
SignalEventExpressionNode: TypeAlias = sl.SignalEventExpressionSyntax
BinaryEventExpressionNode: TypeAlias = sl.BinaryEventExpressionSyntax
ParenthesizedEventExpressionNode: TypeAlias = sl.ParenthesizedEventExpressionSyntax
ImplicitEventControlNode: TypeAlias = sl.ImplicitEventControlSyntax

CaseGenerateNode: TypeAlias = sl.CaseGenerateSyntax
LoopGenerateNode: TypeAlias = sl.LoopGenerateSyntax
IfGenerateNode: TypeAlias = sl.IfGenerateSyntax
GenerateBlockNode: TypeAlias = sl.GenerateBlockSyntax
CaseStatementNode: TypeAlias = sl.CaseStatementSyntax
DefaultCaseItemNode: TypeAlias = sl.DefaultCaseItemSyntax
ConditionalStatementNode: TypeAlias = sl.ConditionalStatementSyntax
ElseClauseNode: TypeAlias = sl.ElseClauseSyntax
BlockStatementNode: TypeAlias = sl.BlockStatementSyntax
EmptyStatementNode: TypeAlias = sl.EmptyStatementSyntax

DataTypeNode: TypeAlias = sl.DataTypeSyntax
KeywordTypeNode: TypeAlias = sl.KeywordTypeSyntax
VirtualInterfaceTypeNode: TypeAlias = sl.VirtualInterfaceTypeSyntax
FunctionPortNode: TypeAlias = sl.FunctionPortSyntax
ArgumentListNode: TypeAlias = sl.ArgumentListSyntax
OrderedArgumentNode: TypeAlias = sl.OrderedArgumentSyntax
NamedArgumentNode: TypeAlias = sl.NamedArgumentSyntax
HierarchyInstantiationNode: TypeAlias = sl.HierarchyInstantiationSyntax
HierarchicalInstanceNode: TypeAlias = sl.HierarchicalInstanceSyntax
PortDeclarationNode: TypeAlias = sl.PortDeclarationSyntax
ImplicitAnsiPortNode: TypeAlias = sl.ImplicitAnsiPortSyntax
PrimitiveDeclarationNode: TypeAlias = sl.UdpDeclarationSyntax
SystemNameNode: TypeAlias = sl.SystemNameSyntax
ClockingDeclarationNode: TypeAlias = sl.ClockingDeclarationSyntax
CheckerDeclarationNode: TypeAlias = sl.CheckerDeclarationSyntax
ModportDeclarationNode: TypeAlias = sl.ModportDeclarationSyntax
SpecifyBlockNode: TypeAlias = sl.SpecifyBlockSyntax
NetAliasNode: TypeAlias = sl.NetAliasSyntax
BindDirectiveNode: TypeAlias = sl.BindDirectiveSyntax
ClassDeclarationNode: TypeAlias = sl.ClassDeclarationSyntax
CovergroupDeclarationNode: TypeAlias = sl.CovergroupDeclarationSyntax
SequenceDeclarationNode: TypeAlias = sl.SequenceDeclarationSyntax
PropertyDeclarationNode: TypeAlias = sl.PropertyDeclarationSyntax
LetDeclarationNode: TypeAlias = sl.LetDeclarationSyntax
ConfigDeclarationNode: TypeAlias = sl.ConfigDeclarationSyntax
RandSequenceStatementNode: TypeAlias = sl.RandSequenceStatementSyntax

DelayNode: TypeAlias = sl.DelaySyntax
Delay3Node: TypeAlias = sl.Delay3Syntax
OneStepDelayNode: TypeAlias = sl.OneStepDelaySyntax
DELAY_CONTROL_NODE_TYPES: tuple[type[SyntaxNode], ...] = (
    DelayNode,
    Delay3Node,
    OneStepDelayNode,
)

ImmediateAssertionStatementNode: TypeAlias = sl.ImmediateAssertionStatementSyntax
ConcurrentAssertionStatementNode: TypeAlias = sl.ConcurrentAssertionStatementSyntax

DPIImportNode: TypeAlias = sl.DPIImportSyntax
DPIExportNode: TypeAlias = sl.DPIExportSyntax
DPI_IMPORT_EXPORT_NODE_TYPES: tuple[type[SyntaxNode], ...] = (
    DPIImportNode,
    DPIExportNode,
)

QueueDimensionSpecifierNode: TypeAlias = sl.QueueDimensionSpecifierSyntax
VariableDimensionNode: TypeAlias = sl.VariableDimensionSyntax
RangeDimensionSpecifierNode: TypeAlias = sl.RangeDimensionSpecifierSyntax
WildcardDimensionSpecifierNode: TypeAlias = sl.WildcardDimensionSpecifierSyntax
ASSOCIATIVE_ARRAY_DIMENSION_NODE_TYPES: tuple[type[SyntaxNode], ...] = (
    RangeDimensionSpecifierNode,
    WildcardDimensionSpecifierNode,
)

BinaryExpressionNode: TypeAlias = sl.BinaryExpressionSyntax
LiteralExpressionNode: TypeAlias = sl.LiteralExpressionSyntax
IntegerVectorExpressionNode: TypeAlias = sl.IntegerVectorExpressionSyntax
LITERAL_EXPRESSION_NODE_TYPES: tuple[type[SyntaxNode], ...] = (
    LiteralExpressionNode,
    IntegerVectorExpressionNode,
)
ElementSelectExpressionNode: TypeAlias = sl.ElementSelectExpressionSyntax
SELECT_EXPRESSION_NODE_TYPES: tuple[type[SyntaxNode], ...] = (
    IdentifierSelectNameNode,
    ElementSelectExpressionNode,
)

__all__ = [
    "ASSOCIATIVE_ARRAY_DIMENSION_NODE_TYPES",
    "ArgumentListNode",
    "BinaryEventExpressionNode",
    "BinaryExpressionNode",
    "BindDirectiveNode",
    "BlockStatementNode",
    "CaseGenerateNode",
    "CaseStatementNode",
    "CheckerDeclarationNode",
    "ClassDeclarationNode",
    "ClockingDeclarationNode",
    "ConcurrentAssertionStatementNode",
    "ConditionalStatementNode",
    "ConfigDeclarationNode",
    "CovergroupDeclarationNode",
    "DELAY_CONTROL_NODE_TYPES",
    "DPIExportNode",
    "DPIImportNode",
    "DPI_IMPORT_EXPORT_NODE_TYPES",
    "DataTypeNode",
    "DeclaratorNode",
    "DefaultCaseItemNode",
    "Delay3Node",
    "DelayNode",
    "DoWhileStatementNode",
    "ElementSelectExpressionNode",
    "ElseClauseNode",
    "EmptyStatementNode",
    "ForLoopStatementNode",
    "ForeverStatementNode",
    "ForwardTypedefDeclarationNode",
    "FunctionDeclarationNode",
    "FunctionPortNode",
    "GenerateBlockNode",
    "HierarchicalInstanceNode",
    "HierarchyInstantiationNode",
    "IDENTIFIER_NAME_NODE_TYPES",
    "IdentifierNameNode",
    "IdentifierSelectNameNode",
    "IfGenerateNode",
    "ImmediateAssertionStatementNode",
    "ImplicitAnsiPortNode",
    "ImplicitEventControlNode",
    "IntegerVectorExpressionNode",
    "JumpStatementNode",
    "KeywordTypeNode",
    "LITERAL_EXPRESSION_NODE_TYPES",
    "LetDeclarationNode",
    "LiteralExpressionNode",
    "LoopGenerateNode",
    "LoopStatementNode",
    "ModportDeclarationNode",
    "ModuleDeclarationNode",
    "NamedArgumentNode",
    "NetAliasNode",
    "OneStepDelayNode",
    "OrderedArgumentNode",
    "PackageImportDeclarationNode",
    "ParenthesizedEventExpressionNode",
    "PortDeclarationNode",
    "PrimitiveDeclarationNode",
    "ProceduralBlockNode",
    "PropertyDeclarationNode",
    "QueueDimensionSpecifierNode",
    "RandSequenceStatementNode",
    "RangeDimensionSpecifierNode",
    "RangeSelectNode",
    "RawNode",
    "ReturnStatementNode",
    "SELECT_EXPRESSION_NODE_TYPES",
    "SequenceDeclarationNode",
    "SignalEventExpressionNode",
    "SpecifyBlockNode",
    "StructUnionTypeNode",
    "SyntaxNode",
    "SyntaxTree",
    "SystemNameNode",
    "Token",
    "TypedefDeclarationNode",
    "VariableDimensionNode",
    "VirtualInterfaceTypeNode",
    "WaitStatementNode",
    "WildcardDimensionSpecifierNode",
]

