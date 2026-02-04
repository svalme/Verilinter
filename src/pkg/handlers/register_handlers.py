# src/pkg/ast/register_handlers.py

from ..ast.dispatch import dispatch

from .default_handler import DefaultHandler

from .token_handler import TokenHandler
from .syntax_node_handler import SyntaxNodeHandler
from .module_declaration_handler import ModuleDeclarationHandler

# blocks
from .procedural_block_handler import ProceduralBlockHandler
from .case_generate_handler import CaseGenerateHandler

#  variables
from .signal_event_expression_handler import SignalEventExpressionHandler
from .declarator_handler import DeclaratorHandler
from .identifier_name_handler import IdentifierNameHandler
