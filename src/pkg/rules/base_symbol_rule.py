from abc import abstractmethod
from typing import Any

from ..semantic.symbol_table import SymbolTable
from .base_diagnostic import BaseDiagnostic


class BaseSymbolRule(BaseDiagnostic):
    @abstractmethod
    def run(self, symbol_table: SymbolTable) -> list[dict[str, Any]]: ...
