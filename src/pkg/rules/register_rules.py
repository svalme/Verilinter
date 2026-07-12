# src/pkg/rules/register_rules.py

from .syntax.rule_runner import rule_runner
from .symbol.symbol_rule_runner import symbol_rule_runner
from .module.module_rule_runner import module_rule_runner

# syntax rules (fire during the walk)
from .syntax.no_blocking_sequential_logic import NoBlockingAssignmentInSequentialRule
from .syntax.no_nonblocking_comb import NoNonBlockingAssignmentInCombRule
from .syntax.default_case import DefaultCaseRule

# symbol rules (single-file, post-walk)
from .symbol.unused_variable_rule import UnusedVariableRule
from .symbol.undeclared_variable import UndeclaredVariableRule
from .symbol.redeclared_variable import RedeclaredVariableRule
from .symbol.read_before_write_rule import ReadBeforeWriteRule

# module rules (cross-file)
from .module.duplicate_module_definition import DuplicateModuleDefinitionRule
from .module.undefined_module import UndefinedModuleRule
