from abc import abstractmethod
from ..ast.symbol_table import SymbolTable
from .base_diagnostic import BaseDiagnostic


class BaseSymbolRule(BaseDiagnostic):

    @abstractmethod
    def run(self, symbol_table: SymbolTable) -> list[dict]: ...