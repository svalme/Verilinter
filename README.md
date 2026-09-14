# Verilinter

A static analysis framework for SystemVerilog, using pyslang. Pyslang parses source code into an AST. The framework walks the tree, builds semantic context (symbol table, scopes, symbols), and applies linting rules over the structure.

## Features
- Tracks lexical scopes (modules, blocks, always blocks, etc.)
- Tracks symbols (variables, signals, ports)
- Supports rule-based analysis (lint-style checks)
- Surfaces syntax and parser errors directly as `PARSER_ERROR` diagnostics and exits non-zero, suppressing corrupt AST walks
- Lints multiple files or a whole directory in one run, with a shared symbol table across them -- enables cross-file checks (e.g. duplicate module names)
- Supports built-in rule profiles plus explicit rule / category filtering
- Supports plain-text, JSON, and SARIF output
- Supports repo-local `.verilinter.toml` configuration and JSON baselines
- Supports multi-process linting with `-j`
- Supports connection reporting for module-to-module wiring and port status
- Supports an optional local SQLite analysis store for caching and persisted run summaries

## Rules Implemented
A basic set of rules are implemented. Right now, it checks for: 
- Non-blocking assignments in combinational logic.
- Blocking assignments in sequential logic.
- Mixed blocking and non-blocking assignment styles in the same procedural block.
- `casex` / `casez` usage.
- Read before write for variables.
- Undeclared variables.
- Unused variables.
- Redeclared variables.
- Default case in a case statement.
- Duplicate module definitions across files.
- Instantiation of a module that isn't defined anywhere in the linted files.
- Self-assignment.
- Multiple non-blocking writes to the same target in one procedural block.
- Duplicate `case` items.
- Unconnected instance ports.
- Duplicate named port connections.
- Mixed named and ordered port connection styles.
- Wildcard port connections.
- Ordered parameter overrides.
- Port width mismatches on instance connections.
- Port signedness mismatches on instance connections.

See [RULES.md](docs/RULES.md) for the maintained rule catalog and the specific cases each rule covers.
See [CLI.md](docs/CLI.md) for the full command-line reference.
See [STORAGE.md](docs/STORAGE.md) for the local SQLite schema and cache/run-store design.
See [RULE_IMPLEMENTATION.md](docs/RULE_IMPLEMENTATION.md) for contributor-facing notes on when rules need parser helpers, handlers, or semantic-model updates.
See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for coding-style requirements (type annotations, design patterns).

## Setup

Create and activate a virtual environment, then install Verilinter in editable mode:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
```

macOS / Linux:

```bash
source .venv/bin/activate
python -m pip install -e .[dev]
```

## Try It Out
### Go to the root directory in terminal and type:

```bash
verilinter <file.v>
```

or

```bash
verilinter <file.sv>
```

Example (single file): 
```bash
verilinter tests/data/simple.v
```

Example (multiple files, or a directory):
```bash
verilinter tests/data/dup_module_a.v tests/data/dup_module_b.v
```

Ordinary lint runs automatically include cross-file module connection diagnostics and module-instantiation style checks.
`verilinter --report connections ...` is only an alternate structural report view; it does not enable a separate checker.

Rule/profile selection:

```bash
verilinter --profile rtl_strict tests/data/simple.v
verilinter --rule NO_SELF_ASSIGNMENT --rule NO_MULTIPLE_NONBLOCKING_WRITES tests/data
verilinter --category rtl_correctness tests/data
```

Machine-readable output:

```bash
verilinter --format json tests/data/self_assignment.v
verilinter --format sarif tests/data
```

Baseline workflow:

```bash
verilinter --write-baseline .verilinter-baseline.json tests/data
verilinter --baseline .verilinter-baseline.json tests/data
```

Connection summary report:

```bash
verilinter --report connections tests/data
```

SQLite-backed local store:

```bash
verilinter --store .verilinter.sqlite tests/data
verilinter --store .verilinter.sqlite --report connections tests/data
verilinter --store .verilinter.sqlite --no-cache tests/data
```

You can still run the script directly if you prefer:

```bash
python src/run_lint.py tests/data/simple.v
```

### Test it with pytest:

```bash
python -m pytest
```

See `docs/TESTING.md` for what kinds of tests exist and where new ones belong.

## Configuration

Verilinter will automatically load `.verilinter.toml` or `verilinter.toml` from the current directory or one of its parents.
Command-line flags are intended to override config-file values, including explicit default-like choices such as `--format text` and `--jobs 1`.

Example:

```toml
[verilinter]
profile = "rtl_strict"
format = "json"
jobs = 4
rules = ["NO_SELF_ASSIGNMENT", "NO_MULTIPLE_NONBLOCKING_WRITES"]
baseline = ".verilinter-baseline.json"
store = ".verilinter.sqlite"
cache = true

[verilinter.severity]
NO_SELF_ASSIGNMENT = "error"
NO_DUPLICATE_CASE_ITEM = "warning"
```
