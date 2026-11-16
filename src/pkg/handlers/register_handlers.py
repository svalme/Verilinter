# src/pkg/handlers/register_handlers.py

from ..walk.dispatch import dispatch

from .default_handler import DefaultHandler

from .token_handler import TokenHandler
from .syntax_node_handler import SyntaxNodeHandler
from .declarations.module_declaration_handler import ModuleDeclarationHandler
from .declarations.function_declaration_handler import FunctionDeclarationHandler
from .declarations.package_import_handler import PackageImportHandler
from .declarations.primitive_declaration_handler import PrimitiveDeclarationHandler

# blocks
from .declarations.clocking_declaration_handler import ClockingDeclarationHandler
from .statements.procedural_block_handler import ProceduralBlockHandler
from .statements.case_statement_handler import CaseStatementHandler
from .statements.case_generate_handler import CaseGenerateHandler
from .statements.block_statement_handler import BlockStatementHandler
from .statements.for_loop_statement_handler import ForLoopStatementHandler
from .statements.type_and_generate_scope_handler import (
    GenerateBlockHandler,
    GenvarDeclarationHandler,
    LoopGenerateHandler,
    StructUnionTypeHandler,
)
from .declarations.typedef_declaration_handler import TypedefDeclarationHandler
from .statements.return_statement_handler import ReturnStatementHandler

#  variables
from .statements.signal_event_expression_handler import SignalEventExpressionHandler
from .declarations.declarator_handler import DeclaratorHandler
from .identifier_name_handler import IdentifierNameHandler

# instantiation
from .hierarchy_instantiation_handler import HierarchyInstantiationHandler
