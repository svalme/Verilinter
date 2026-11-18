"""Creating the store's tables and migrating an older layout to the current one."""
from __future__ import annotations

import sqlite3

from .cache import CACHE_DDL
from .connection import StoreConnection
from .elaboration import ELABORATION_DDL
from .history import HISTORY_DDL

SCHEMA_VERSION = "4"

_META_DDL = """
    CREATE TABLE IF NOT EXISTS schema_meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
"""


def ensure_schema(connection: StoreConnection) -> None:
    """Create the tables, or migrate an older layout, inside one write transaction."""
    with connection.exclusive_transaction() as conn:
        apply_schema(conn)


def apply_schema(conn: sqlite3.Connection) -> None:
    # The statements contain no embedded semicolons, so splitting is safe.
    for script in (_META_DDL, CACHE_DDL, ELABORATION_DDL, HISTORY_DDL):
        for statement in script.split(";"):
            if statement.strip():
                conn.execute(statement)
    existing_version = read_schema_version(conn)
    if existing_version is None:
        conn.execute(
            """
            INSERT INTO schema_meta(key, value)
            VALUES ('schema_version', ?)
            """,
            (SCHEMA_VERSION,),
        )
        return

    migrate_schema(conn, existing_version)


def read_schema_version(conn: sqlite3.Connection) -> str | None:
    row = conn.execute(
        """
        SELECT value
        FROM schema_meta
        WHERE key = 'schema_version'
        """
    ).fetchone()
    if row is None:
        return None
    return str(row["value"])


def migrate_schema(conn: sqlite3.Connection, existing_version: str) -> None:
    if existing_version == SCHEMA_VERSION:
        return

    migrations = {
        "0": migrate_0_to_1,
        "1": migrate_1_to_2,
        "2": migrate_2_to_3,
        "3": migrate_3_to_4,
    }

    version = existing_version
    while version != SCHEMA_VERSION:
        migration = migrations.get(version)
        if migration is None:
            raise ValueError(
                "analysis store schema version mismatch: "
                f"found {existing_version}, expected {SCHEMA_VERSION}. "
                "No migration path is available. Use a fresh --store path or rebuild the existing store."
            )
        version = migration(conn)


def migrate_0_to_1(conn: sqlite3.Connection) -> str:
    conn.execute(
        """
        UPDATE schema_meta
        SET value = '1'
        WHERE key = 'schema_version'
        """
    )
    return "1"

def migrate_1_to_2(conn: sqlite3.Connection) -> str:
    """Add ON DELETE CASCADE to the analysis_run_* child tables so
    prune_runs no longer has to delete children in a hand-maintained order."""
    rebuilds = {
        "analysis_run_files": """
            CREATE TABLE analysis_run_files_v2 (
                run_id INTEGER NOT NULL,
                ordinal INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                cache_hit INTEGER NOT NULL,
                PRIMARY KEY (run_id, ordinal),
                FOREIGN KEY (run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
            )
        """,
        "analysis_run_diagnostics": """
            CREATE TABLE analysis_run_diagnostics_v2 (
                run_id INTEGER NOT NULL,
                ordinal INTEGER NOT NULL,
                code TEXT NOT NULL,
                category TEXT,
                severity TEXT,
                file TEXT,
                line INTEGER NOT NULL,
                col INTEGER NOT NULL,
                message TEXT NOT NULL,
                PRIMARY KEY (run_id, ordinal),
                FOREIGN KEY (run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
            )
        """,
        "analysis_run_modules": """
            CREATE TABLE analysis_run_modules_v2 (
                run_id INTEGER NOT NULL,
                ordinal INTEGER NOT NULL,
                module_name TEXT NOT NULL,
                file TEXT,
                line INTEGER NOT NULL,
                col INTEGER NOT NULL,
                PRIMARY KEY (run_id, ordinal),
                FOREIGN KEY (run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
            )
        """,
        "analysis_run_instantiations": """
            CREATE TABLE analysis_run_instantiations_v2 (
                run_id INTEGER NOT NULL,
                ordinal INTEGER NOT NULL,
                parent_module TEXT,
                child_module TEXT,
                instance_name TEXT,
                file TEXT,
                line INTEGER NOT NULL,
                col INTEGER NOT NULL,
                connection_style TEXT,
                PRIMARY KEY (run_id, ordinal),
                FOREIGN KEY (run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
            )
        """,
        "analysis_run_connections": """
            CREATE TABLE analysis_run_connections_v2 (
                run_id INTEGER NOT NULL,
                instantiation_ordinal INTEGER NOT NULL,
                ordinal INTEGER NOT NULL,
                kind TEXT NOT NULL,
                port_name TEXT,
                expr_text TEXT,
                expr_name TEXT,
                expr_width INTEGER,
                expr_signed INTEGER,
                file TEXT,
                line INTEGER NOT NULL,
                col INTEGER NOT NULL,
                PRIMARY KEY (run_id, instantiation_ordinal, ordinal),
                FOREIGN KEY (run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
            )
        """,
    }

    for table, create_sql in rebuilds.items():
        conn.execute(create_sql)
        conn.execute(f"INSERT INTO {table}_v2 SELECT * FROM {table}")
        conn.execute(f"DROP TABLE {table}")
        conn.execute(f"ALTER TABLE {table}_v2 RENAME TO {table}")

    conn.execute(
        """
        UPDATE schema_meta
        SET value = '2'
        WHERE key = 'schema_version'
        """
    )
    return "2"

def migrate_2_to_3(conn: sqlite3.Connection) -> str:
    """Add header_dependencies_json to cached_file_analysis to track
    transitive preprocessor dependencies."""
    cols = [r[1] for r in conn.execute("PRAGMA table_info(cached_file_analysis)").fetchall()]
    if "header_dependencies_json" not in cols:
        conn.execute(
            """
            ALTER TABLE cached_file_analysis
            ADD COLUMN header_dependencies_json TEXT DEFAULT '[]'
            """
        )
    conn.execute(
        """
        UPDATE cached_file_analysis
        SET header_dependencies_json = '[]'
        WHERE header_dependencies_json IS NULL
        """
    )
    conn.execute(
        """
        UPDATE schema_meta
        SET value = '3'
        WHERE key = 'schema_version'
        """
    )
    return "3"


def migrate_3_to_4(conn: sqlite3.Connection) -> str:
    """The elaboration cache table (`cached_elaboration`) is created with the other tables; only the version moves."""
    conn.execute(
        """
        UPDATE schema_meta
        SET value = '4'
        WHERE key = 'schema_version'
        """
    )
    return "4"
