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
ProceduralBlockNode: TypeAlias = sl.ProceduralBlockSyntax
SignalEventExpressionNode: TypeAlias = sl.SignalEventExpressionSyntax
CaseGenerateNode: TypeAlias = sl.CaseGenerateSyntax
HierarchyInstantiationNode: TypeAlias = sl.HierarchyInstantiationSyntax
HierarchicalInstanceNode: TypeAlias = sl.HierarchicalInstanceSyntax
DefaultCaseItemNode: TypeAlias = sl.DefaultCaseItemSyntax
PortDeclarationNode: TypeAlias = sl.PortDeclarationSyntax
