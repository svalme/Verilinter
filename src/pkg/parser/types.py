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

HierarchyInstantiationNode: TypeAlias = sl.HierarchyInstantiationSyntax
HierarchicalInstanceNode: TypeAlias = sl.HierarchicalInstanceSyntax
PortDeclarationNode: TypeAlias = sl.PortDeclarationSyntax
PrimitiveDeclarationNode: TypeAlias = sl.UdpDeclarationSyntax
SystemNameNode: TypeAlias = sl.SystemNameSyntax

__all__ = [
    "BinaryEventExpressionNode",
    "CaseGenerateNode",
    "CaseStatementNode",
    "DeclaratorNode",
    "DefaultCaseItemNode",
    "HierarchicalInstanceNode",
    "HierarchyInstantiationNode",
    "IDENTIFIER_NAME_NODE_TYPES",
    "IdentifierNameNode",
    "IdentifierSelectNameNode",
    "IfGenerateNode",
    "ImplicitEventControlNode",
    "LoopGenerateNode",
    "ModuleDeclarationNode",
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
]
