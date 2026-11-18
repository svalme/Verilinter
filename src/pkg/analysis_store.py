"""The local analysis store, composed from its parts.

`AnalysisStore` is the one object the pipeline and the CLI hold. The work is in `store/`: `connection`
(opening the file), `schema` (tables and migrations), `cache` (reusable per-file results), `elaboration` (the whole-set width record) and `history`
(recorded runs). Each part has its own version token: `ANALYZER_CACHE_VERSION` for the cache and
`SCHEMA_VERSION` for the table layout.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .rules.rule_selection import RuleSelection
from .semantic.symbol_table import SymbolTable
from .store.cache import FileAnalysisCache
from .store.connection import BUSY_TIMEOUT_SECONDS, StoreConnection
from .store.elaboration import ElaborationCache
from .store.history import RunHistory
from .store.keys import ANALYZER_CACHE_VERSION, file_sha256, selection_key
from .store.schema import SCHEMA_VERSION, ensure_schema
from .store.timestamps import utc_now_iso

__all__ = [
    "ANALYZER_CACHE_VERSION",
    "AnalysisStore",
    "BUSY_TIMEOUT_SECONDS",
    "SCHEMA_VERSION",
    "file_sha256",
    "selection_key",
    "utc_now_iso",
]


class AnalysisStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.connection = StoreConnection(path)
        ensure_schema(self.connection)
        self.cache = FileAnalysisCache(self.connection)
        self.elaboration = ElaborationCache(self.connection)
        self.history = RunHistory(self.connection)

    def load_cached_worker_result(
        self,
        *,
        file_path: str,
        file_hash: str,
        rule_selection: RuleSelection | None,
        include_dirs: list[str] | None = None,
        package_registry_fingerprint: str | None = None,
        defines: list[str] | None = None,
    ) -> dict[str, Any] | None:
        return self.cache.load(
            file_path=file_path,
            file_hash=file_hash,
            rule_selection=rule_selection,
            include_dirs=include_dirs,
            package_registry_fingerprint=package_registry_fingerprint,
            defines=defines,
        )

    def store_cached_worker_result(
        self,
        *,
        file_path: str,
        file_hash: str,
        rule_selection: RuleSelection | None,
        worker_result: dict[str, Any],
        include_dirs: list[str] | None = None,
        package_registry_fingerprint: str | None = None,
        defines: list[str] | None = None,
        header_dependencies: list[dict[str, str]] | None = None,
    ) -> None:
        self.cache.store(
            file_path=file_path,
            file_hash=file_hash,
            rule_selection=rule_selection,
            worker_result=worker_result,
            include_dirs=include_dirs,
            package_registry_fingerprint=package_registry_fingerprint,
            defines=defines,
            header_dependencies=header_dependencies,
        )

    def record_run(
        self,
        *,
        cwd: str,
        fmt: str,
        report_kind: str | None,
        jobs: int,
        rule_selection: RuleSelection | None,
        baseline_path: str | None,
        file_records: list[dict[str, Any]],
        diagnostics: list[dict[str, Any]],
        symbol_table: SymbolTable,
    ) -> int:
        return self.history.record_run(
            cwd=cwd,
            fmt=fmt,
            report_kind=report_kind,
            jobs=jobs,
            rule_selection=rule_selection,
            baseline_path=baseline_path,
            file_records=file_records,
            diagnostics=diagnostics,
            symbol_table=symbol_table,
        )

    def load_cached_elaboration(self, *, set_id: str, input_key: str) -> dict[str, Any] | None:
        return self.elaboration.load(set_id=set_id, input_key=input_key)

    def store_cached_elaboration(self, *, set_id: str, input_key: str, payload: dict[str, Any]) -> None:
        self.elaboration.store(set_id=set_id, input_key=input_key, payload=payload)

    def prune_cache(self, *, older_than_days: int) -> int:
        self.elaboration.prune(older_than_days=older_than_days)
        return self.cache.prune(older_than_days=older_than_days)

    def prune_runs(self, *, keep_last: int) -> int:
        return self.history.prune(keep_last=keep_last)

    def vacuum(self) -> None:
        conn = self.connection.connect()
        try:
            conn.execute("VACUUM")
        finally:
            conn.close()

    def status(self) -> dict[str, Any]:
        size_bytes = self.path.stat().st_size if self.path.exists() else 0
        return {
            "path": str(self.path),
            "size_bytes": size_bytes,
            "cached_files": self.cache.count(),
            "recorded_runs": self.history.count(),
        }
