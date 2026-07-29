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
BinaryEventExpressionNode: TypeAlias = sl.BinaryEventExpressionSyntax
ParenthesizedEventExpressionNode: TypeAlias = sl.ParenthesizedEventExpressionSyntax
ImplicitEventControlNode: TypeAlias = sl.ImplicitEventControlSyntax
CaseGenerateNode: TypeAlias = sl.CaseGenerateSyntax
LoopGenerateNode: TypeAlias = sl.LoopGenerateSyntax
CaseStatementNode: TypeAlias = sl.CaseStatementSyntax
HierarchyInstantiationNode: TypeAlias = sl.HierarchyInstantiationSyntax
HierarchicalInstanceNode: TypeAlias = sl.HierarchicalInstanceSyntax
DefaultCaseItemNode: TypeAlias = sl.DefaultCaseItemSyntax
PortDeclarationNode: TypeAlias = sl.PortDeclarationSyntax
IfGenerateNode: TypeAlias = sl.IfGenerateSyntax
