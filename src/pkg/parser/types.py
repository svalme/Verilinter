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
CaseStatementNode: TypeAlias = sl.CaseStatementSyntax
DefaultCaseItemNode: TypeAlias = sl.DefaultCaseItemSyntax

DataTypeNode: TypeAlias = sl.DataTypeSyntax
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
BinaryExpressionNode: TypeAlias = sl.BinaryExpressionSyntax

__all__ = [
    "ArgumentListNode",
    "BinaryEventExpressionNode",
    "BinaryExpressionNode",
    "CaseGenerateNode",
    "CaseStatementNode",
    "ClockingDeclarationNode",
    "DataTypeNode",
    "DeclaratorNode",
    "DefaultCaseItemNode",
    "ForLoopStatementNode",
    "ForeverStatementNode",
    "LoopStatementNode",
    "DoWhileStatementNode",
    "JumpStatementNode",
    "ReturnStatementNode",
    "WaitStatementNode",
    "RangeSelectNode",
    "ForwardTypedefDeclarationNode",
    "FunctionDeclarationNode",
    "FunctionPortNode",
    "StructUnionTypeNode",
    "LoopGenerateNode",
    "HierarchicalInstanceNode",
    "HierarchyInstantiationNode",
    "IDENTIFIER_NAME_NODE_TYPES",
    "IdentifierNameNode",
    "IdentifierSelectNameNode",
    "IfGenerateNode",
    "ImplicitAnsiPortNode",
    "ImplicitEventControlNode",
    "ModuleDeclarationNode",
    "NamedArgumentNode",
    "OrderedArgumentNode",
    "PackageImportDeclarationNode",
    "ParenthesizedEventExpressionNode",
    "PortDeclarationNode",
    "PrimitiveDeclarationNode",
    "ProceduralBlockNode",
    "RawNode",
    "SignalEventExpressionNode",
    "SyntaxNode",
    "SyntaxTree",
    "SystemNameNode",
    "Token",
    "TypedefDeclarationNode",
]
