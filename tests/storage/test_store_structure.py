"""The store's parts stay separate: the cache and the run history do not know about each other."""
from __future__ import annotations

import ast
from pathlib import Path

from src.pkg.store.cache import FileAnalysisCache
from src.pkg.store.connection import StoreConnection
from src.pkg.store.history import RunHistory
from src.pkg.store.schema import ensure_schema
from tests.support.scratch import make_scratch

STORE_DIR = Path(__file__).resolve().parents[2] / "src" / "pkg" / "store"


def _imported_store_modules(filename: str) -> set[str]:
    tree = ast.parse((STORE_DIR / filename).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
            imported.add(node.module)
    return imported


def test_the_cache_does_not_import_the_history() -> None:
    assert "history" not in _imported_store_modules("cache.py")


def test_the_history_does_not_import_the_cache() -> None:
    assert "cache" not in _imported_store_modules("history.py")


def test_the_connection_knows_no_tables() -> None:
    assert _imported_store_modules("connection.py") == set()


def test_each_part_works_without_the_other() -> None:
    path = make_scratch("_tmp_store_structure", "parts") / "verilinter.sqlite"
    connection = StoreConnection(path)
    ensure_schema(connection)

    assert FileAnalysisCache(connection).count() == 0
    assert RunHistory(connection).count() == 0
