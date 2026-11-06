"""Opening the store file: connections, transactions and the write-ahead-log switch."""
from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

BUSY_TIMEOUT_SECONDS = 30.0
_WAL_RETRY_DELAY_SECONDS = 0.02
_WAL_RETRY_ATTEMPTS = int(BUSY_TIMEOUT_SECONDS / _WAL_RETRY_DELAY_SECONDS)


class StoreConnection:
    """Knows where the store file is and how to open it; knows nothing about what the tables hold."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=BUSY_TIMEOUT_SECONDS)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(f"PRAGMA busy_timeout = {int(BUSY_TIMEOUT_SECONDS * 1000)}")
        return conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    @contextmanager
    def exclusive_transaction(self) -> Iterator[sqlite3.Connection]:
        """A write transaction taken up front, after switching the file to WAL mode.

        A crash or error rolls the whole transaction back, and concurrent openers take turns on the write lock.
        """
        conn = self.connect()
        conn.isolation_level = None
        try:
            self._enable_wal(conn)
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                conn.execute("COMMIT")
            except BaseException:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise
        finally:
            conn.close()

    @staticmethod
    def _enable_wal(conn: sqlite3.Connection) -> None:
        # Switching a database file into WAL mode needs a lock that SQLite does not
        # wait for with the busy timeout, so concurrent first openers can see
        # "database is locked" immediately. Retry for the same budget the other
        # statements get.
        last_error: sqlite3.OperationalError | None = None
        for _ in range(_WAL_RETRY_ATTEMPTS):
            if str(conn.execute("PRAGMA journal_mode").fetchone()[0]).lower() == "wal":
                return
            try:
                conn.execute("PRAGMA journal_mode = WAL").fetchone()
                return
            except sqlite3.OperationalError as exc:
                if "locked" not in str(exc):
                    raise
                last_error = exc
                time.sleep(_WAL_RETRY_DELAY_SECONDS)
        assert last_error is not None
        raise last_error
