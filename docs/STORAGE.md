# Verilinter Local Storage

Verilinter can persist analysis results and reuse cached per-file work through a local SQLite database.

This storage is opt-in through:
- `--store PATH`
- the `store = "..."` config field

## Goals

The local store is designed to help with:
- reusing unchanged per-file analysis results
- recording full lint runs
- recording module / instantiation / connection summaries
- keeping the storage local and dependency-free

Ordinary lint runs and `--report connections` both use the same underlying analysis pipeline.
The store therefore helps both flows automatically; users do not need a special "module-checking mode"
to get connection diagnostics.

## Cache Model

The cache is keyed by:
- absolute file path
- file content SHA-256
- rule-selection signature
- analyzer cache version token
- include directory search order (`-I`)
- preprocessor macro defines (`-D`)
- package registry fingerprint (corpus package declarations and signatures)
- direct and transitive header dependencies (paths and SHA-256 hashes of all ` `include ` files)

That means a cached entry is reused only when:
1. the file path is the same
2. the file contents are unchanged
3. the effective rule selection is unchanged
4. the analyzer cache version is unchanged
5. the include directory configuration and macro defines match
6. corpus package declarations have not shifted
7. all directly and transitively included header files exist on disk with unchanged SHA-256 hashes

The analyzer cache version is a small internal compatibility token for Verilinter's own analysis pipeline.
When parser behavior, symbol-building behavior, cached payload shape, or rule logic changes in a way that
could make old worker results unsafe to reuse, this token should be bumped so cached per-file rows refresh
on the next run even if the input files themselves did not change.

Severity overrides are applied after cached worker results are loaded, so they do not invalidate the per-file analysis cache.

## Schema

The current schema version is `3`.

Verilinter treats schema compatibility separately from cache compatibility:
- `ANALYZER_CACHE_VERSION` controls whether cached per-file analysis blobs are still safe to reuse (currently `2026-10-06-symbol-serialization-and-port-inheritance`)
- `SCHEMA_VERSION` controls whether the SQLite table layout is still compatible with the current code

If Verilinter opens a store with an older schema version and a supported migration path exists, it upgrades the
database in place before continuing. If no migration path exists, it fails fast with a clear error telling the
user to use a fresh store path or rebuild the existing store. That protects against reading relational tables
whose layout no longer matches what the current release expects.

## Versioning Policy

Use `ANALYZER_CACHE_VERSION` when:
- parser behavior changes
- symbol-building behavior changes
- rule logic changes in a way that can alter per-file worker results
- cached JSON payload shape changes and old cache blobs should be refreshed

Use `SCHEMA_VERSION` when:
- a table is added, removed, or renamed
- a column is added, removed, renamed, or repurposed
- relational constraints or persisted row semantics change

Current migration policy:
- durable run-history tables should be migrated forward when practical
- disposable cache rows may be invalidated instead of migrated
- unsupported schema versions should fail clearly rather than being guessed at

Current supported schema migrations:
- `0 -> 1`: Initial store layout migration
- `1 -> 2`: Cascade deletion (`ON DELETE CASCADE`) across run child tables
- `2 -> 3`: Transitive header dependency tracking (`header_dependencies_json`)

Rebuild guidance:
- use `--no-cache` when you want a fresh analysis pass without deleting the store
- use a fresh `--store` path or delete the old store when a schema version has no supported migration path
- bump `ANALYZER_CACHE_VERSION` instead of `SCHEMA_VERSION` when only cache compatibility changed

## Refresh Behavior

Current refresh behavior is:
- every requested file path is still discovered and hashed on each run
- unchanged files can reuse cached per-file worker results (`cache_hit: true`)
- changed files are re-parsed and re-analyzed (`cache_hit: false`)
- cross-file module rules are rerun over the reconstructed batch view each time

### Partial Refresh Semantics & Cross-File Parity
When a subset of files in a multi-file project is modified, Verilinter executes a **partial refresh** (`hits: M, misses: K`). Diagnostics produced under partial refreshes maintain 100% equivalence with fresh (`--no-cache`) runs because:
1. **Hybrid Symbol Table Reconstruction**: The cross-file `SymbolTable` seamlessly merges module scopes, symbols, and instantiation edges loaded from SQLite with those produced by fresh worker AST walks.
2. **Dynamic Interface Re-Evaluation**: If a submodule renames or adds a port variable (e.g., `din_i` $\rightarrow$ `din_val_i`), an unchanged caller module retrieved from SQLite is re-evaluated against the new submodule interface. The cross-file engine accurately surfaces `UNKNOWN_NAMED_PORT_CONNECTION` and `NO_UNCONNECTED_INSTANCE_PORTS` on the caller even though the caller file was not re-parsed.
3. **Collision & Cross-File Invariant Checking**: Cross-file rules such as `DUPLICATE_MODULE`, `PORT_CONNECTION_WIDTH_MISMATCH`, and `NO_UNDRIVEN_SIGNAL` execute across both cached and fresh module records identically to cold runs.

Verilinter avoids repeated parsing and walking for unchanged files without a VCS-aware index or a separate "changed files only" database. It does not do Git-index-aware candidate selection, file watching, or whole-repo incremental scheduling.

## Retention and Maintenance

Stores are created or migrated automatically when a lint run uses `--store PATH`. Cached file results and
recorded run history are retained until you remove them; Verilinter does not apply automatic retention.

Use the maintenance flags with `--store`; source paths are not required. Each command performs its work and then exits:

```bash
# Remove cached per-file results older than 30 days.
verilinter --store .verilinter.sqlite --prune-cache-days 30

# Keep the 100 most recently recorded runs and remove older run history.
verilinter --store .verilinter.sqlite --prune-runs-keep 100

# Reclaim unused SQLite pages after pruning.
verilinter --store .verilinter.sqlite --vacuum-store
```

The maintenance flags can be combined. They run in this order: cache pruning, run-history pruning, then vacuuming.
For example, a periodic cleanup can prune both kinds of data and reclaim the resulting disk space in one command:

```bash
verilinter --store .verilinter.sqlite --prune-cache-days 30 --prune-runs-keep 100 --vacuum-store
```

`--prune-cache-days` affects only reusable per-file cache entries. `--prune-runs-keep` removes older recorded
run summaries and their associated rows. `--vacuum-store` preserves remaining data but may take longer for a
large store, so it is most useful after pruning rather than on every lint run.

## Single Store Design

Separate databases for "input-file edits" versus "analyzer-version edits" are not required by the current
design. The current model keeps one store and distinguishes those cases through:

- file-content hashes for source changes
- `ANALYZER_CACHE_VERSION` for analysis-compatibility changes
- `SCHEMA_VERSION` plus migrations for relational-layout changes

That keeps the user-facing setup simpler while still letting the tool refresh the right parts at the right time.

## Tables

### `schema_meta`

Stores schema metadata.

Columns:
- `key TEXT PRIMARY KEY`
- `value TEXT NOT NULL`

### `cached_file_analysis`

Stores reusable per-file worker results.

Columns:
- `file_path TEXT NOT NULL`
- `file_hash TEXT NOT NULL`
- `selection_key TEXT NOT NULL`
- `cached_at TEXT NOT NULL`
- `worker_result_json TEXT NOT NULL`

Primary key:
- `(file_path, file_hash, selection_key)`

Purpose:
- cache syntax diagnostics
- cache single-file symbol diagnostics
- cache module summaries
- cache instantiation and connection summaries needed for later cross-file passes

### `analysis_runs`

Stores one row per recorded analysis execution.

Columns:
- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `created_at TEXT NOT NULL`
- `cwd TEXT`
- `format TEXT`
- `report_kind TEXT`
- `jobs INTEGER NOT NULL`
- `selection_key TEXT NOT NULL`
- `baseline_path TEXT`

Purpose:
- anchor a persisted lint run or report run

### `analysis_run_files`

Stores the files that participated in a recorded run.

Columns:
- `run_id INTEGER NOT NULL`
- `ordinal INTEGER NOT NULL`
- `file_path TEXT NOT NULL`
- `file_hash TEXT NOT NULL`
- `cache_hit INTEGER NOT NULL`

Primary key:
- `(run_id, ordinal)`

Purpose:
- preserve file order
- track whether each file came from cache or fresh analysis

### `analysis_run_diagnostics`

Stores persisted diagnostics for a run.

Columns:
- `run_id INTEGER NOT NULL`
- `ordinal INTEGER NOT NULL`
- `code TEXT NOT NULL`
- `category TEXT`
- `severity TEXT`
- `file TEXT`
- `line INTEGER NOT NULL`
- `col INTEGER NOT NULL`
- `message TEXT NOT NULL`

Primary key:
- `(run_id, ordinal)`

### `analysis_run_modules`

Stores discovered modules for a run.

Columns:
- `run_id INTEGER NOT NULL`
- `ordinal INTEGER NOT NULL`
- `module_name TEXT NOT NULL`
- `file TEXT`
- `line INTEGER NOT NULL`
- `col INTEGER NOT NULL`

Primary key:
- `(run_id, ordinal)`

### `analysis_run_instantiations`

Stores module instantiations for a run.

Columns:
- `run_id INTEGER NOT NULL`
- `ordinal INTEGER NOT NULL`
- `parent_module TEXT`
- `child_module TEXT`
- `instance_name TEXT`
- `file TEXT`
- `line INTEGER NOT NULL`
- `col INTEGER NOT NULL`
- `connection_style TEXT`

Primary key:
- `(run_id, ordinal)`

### `analysis_run_connections`

Stores per-connection details nested under an instantiation.

Columns:
- `run_id INTEGER NOT NULL`
- `instantiation_ordinal INTEGER NOT NULL`
- `ordinal INTEGER NOT NULL`
- `kind TEXT NOT NULL`
- `port_name TEXT`
- `expr_text TEXT`
- `expr_name TEXT`
- `expr_width INTEGER`
- `expr_signed INTEGER`
- `file TEXT`
- `line INTEGER NOT NULL`
- `col INTEGER NOT NULL`

Primary key:
- `(run_id, instantiation_ordinal, ordinal)`

Purpose:
- preserve the exact port-binding structure that powered lint rules and connection reports

## Example Usage

Create and use a local store:

```bash
verilinter --store .verilinter.sqlite tests/data
```

Use the store but force fresh analysis:

```bash
verilinter --store .verilinter.sqlite --no-cache tests/data
```

Persist a connection report run:

```bash
verilinter --store .verilinter.sqlite --report connections tests/data
```

## Config

Example:

```toml
[verilinter]
store = ".verilinter.sqlite"
cache = true
jobs = 4
```

Supported storage-related config fields:
- `store`
- `cache`

## Tradeoffs

Worker results are stored as JSON blobs inside the cache table, while recorded run summaries are normalized into relational tables.

That gives us:
- simple cache round-tripping
- inspectable run history
- a stable path to future SQL queries over modules, instantiations, and diagnostics
- one local SQLite file instead of separate cache and history databases
- independent handling for input-file edits versus analyzer-version edits

Cache correctness details:

- Package-export fingerprints invalidate consumers when the visible package
  names change, even if the consumer source did not change.
- Include search order is significant and is preserved in the cache key.
- Direct and transitive `include` dependencies are stored with their SHA-256
  hashes (`header_dependencies_json`), so a changed header invalidates every
  file that includes it, even when the including file did not change.
- Files are parsed with fresh source managers so repeated analyses observe
  edits within the same Python process.
- Analyzer changes invalidate old entries through `ANALYZER_CACHE_VERSION`.

It does not provide automatic cache eviction; see Retention and Maintenance.
