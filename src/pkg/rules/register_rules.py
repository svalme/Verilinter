# src/pkg/rules/register_rules.py

from .syntax.rule_runner import rule_runner
from .symbol.symbol_rule_runner import symbol_rule_runner
from .module.module_rule_runner import module_rule_runner

# syntax rules (fire during the walk)
from .syntax.no_blocking_sequential_logic import NoBlockingAssignmentInSequentialRule
from .syntax.no_nonblocking_comb import NoNonBlockingAssignmentInCombRule
from .syntax.default_case import DefaultCaseRule
from .syntax.no_casex_casez import NoCaseXCaseZRule
from .syntax.no_mixed_assignment_style import NoMixedAssignmentStyleRule
from .syntax.no_initial_block import NoInitialBlockRule
from .syntax.no_final_block import NoFinalBlockRule
from .syntax.no_always_latch import NoAlwaysLatchRule
from .syntax.no_case_generate import NoCaseGenerateRule
from .syntax.no_full_parallel_case import NoFullParallelCaseRule
from .syntax.no_unique_priority_case import NoUniquePriorityCaseRule
from .syntax.no_inout_internal import NoInternalInoutRule
from .syntax.no_latch_in_always_comb import NoLatchInAlwaysCombRule
from .syntax.no_defparam import NoDefparamRule

# symbol rules (single-file, post-walk)
from .symbol.unused_variable_rule import UnusedVariableRule
from .symbol.undeclared_variable import UndeclaredVariableRule
from .symbol.no_implicit_net import NoImplicitNetRule
from .symbol.no_multiple_drivers import NoMultipleDriversRule
from .symbol.no_undriven_signal import NoUndrivenSignalRule
from .symbol.redeclared_variable import RedeclaredVariableRule
from .symbol.read_before_write_rule import ReadBeforeWriteRule

# module rules (cross-file)
from .module.duplicate_module_definition import DuplicateModuleDefinitionRule
from .module.undefined_module import UndefinedModuleRule
