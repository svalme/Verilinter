# Verilinter CLI Reference

This file is the command-line reference for `verilinter`.

## Synopsis

```bash
verilinter [options] <path> [<path> ...]
```

`<path>` can be:
- a `.v` file
- a `.sv` file
- a directory, in which case Verilinter recursively collects `*.v` and `*.sv`

## Basic Usage

Lint one file:

```bash
verilinter tests/data/simple.v
```

Lint several files:

```bash
verilinter tests/data/dup_module_a.v tests/data/dup_module_b.v
```

Lint a directory:

```bash
verilinter tests/data
```

Ordinary lint runs automatically include:
- syntax rules
- symbol / semantic rules
- cross-file module / connection rules
- module-instantiation style rules such as wildcard, ordered-port, and ordered-parameter checks

## Options

### `-j`, `--jobs N`

Use up to `N` worker processes.

```bash
verilinter -j 4 tests/data
```

Notes:
- `N` must be at least `1`
- `1` means sequential execution
- on some environments, process creation can be blocked; in that case Verilinter falls back to sequential execution

### `--profile {all,rtl_strict,sv_rtl_subset,legacy_verilog}`

Enable a built-in rule profile.

```bash
verilinter --profile rtl_strict tests/data
```

### `--rule RULE_CODE`

Enable only the listed rule code or codes.
Repeat the flag to allow multiple rules.

```bash
verilinter --rule NO_SELF_ASSIGNMENT --rule NO_DUPLICATE_CASE_ITEM tests/data
```

### `--category CATEGORY`

Enable only the listed rule category or categories.
Repeat the flag to allow multiple categories.

```bash
verilinter --category rtl_correctness tests/data
```

### `--format {text,json,sarif}`

Choose the diagnostics output format.

```bash
verilinter --format text tests/data
verilinter --format json tests/data
verilinter --format sarif tests/data
```

`text` is the default.

### `-o`, `--output PATH`

Write output directly to a file in UTF-8 encoding instead of printing to standard output.
Parent directories are created automatically if they do not exist.

```bash
verilinter -o reports/lint.sarif --format sarif tests/data
verilinter -o reports/summary.txt --report connections tests/data
```

### `--fail-on-error`

Exit with failure code (`1`) if any unsuppressed diagnostics have `error` severity (or if syntax `PARSER_ERROR`s are present).
Ideal for CI/CD check suites to fail pipelines on severe lint infractions.

```bash
verilinter --fail-on-error tests/data
```

### `--fail-on-warning`

Exit with failure code (`1`) if any unsuppressed diagnostics have `warning` or `error` severity.

```bash
verilinter --fail-on-warning tests/data
```

### `-D`, `--define NAME[=VALUE]`

Define a preprocessor macro for conditional compilation (` `ifdef `, ` `ifndef `, ` `elsif `).
Repeat the flag to supply multiple defines.

```bash
verilinter -D SYNTHESIS -D WIDTH=32 tests/data
```

### `-I`, `--include-dir DIR`

Add an include directory to search when resolving ` `include ` directives outside the source files' immediate directory.
Repeat the flag to add multiple directories.

```bash
verilinter -I include/ -I common/headers/ tests/data
```

### `--exit-zero`

Always exit with status code `0`, even when rule errors, rule warnings, or parser errors are detected.
Useful in reporting pipelines that archive findings without halting pipeline steps.

```bash
verilinter --exit-zero tests/data
```

### `--config PATH`

Load configuration from a specific TOML file.

```bash
verilinter --config .verilinter.toml tests/data
```

If `--config` is not passed, Verilinter automatically looks for:
- `.verilinter.toml`
- `verilinter.toml`

starting in the current directory and then walking upward through parent directories.

Design note:
- CLI flags always take precedence over config-file values, even when the CLI value matches a built-in default such as `--format text` or `--jobs 1`

### `--severity RULE_CODE=LEVEL`

Override the severity of a rule.
Repeat the flag to apply multiple overrides.

Allowed levels:
- `error`
- `warning`
- `info`

```bash
verilinter --severity NO_SELF_ASSIGNMENT=error tests/data
verilinter --severity NO_DUPLICATE_CASE_ITEM=warning --severity NO_SELF_ASSIGNMENT=error tests/data
```

### `--baseline PATH`

Suppress diagnostics that already exist in a JSON baseline file.

```bash
verilinter --baseline .verilinter-baseline.json tests/data
```

### `--write-baseline PATH`

Write the current diagnostics to a JSON baseline file and exit.

```bash
verilinter --write-baseline .verilinter-baseline.json tests/data
```

Note: If any input file contains syntax or parser errors, Verilinter will refuse to write a baseline file, write an error message to `stderr`, and exit with code `1`. This ensures incomplete or corrupted AST findings are never recorded into a baseline.

### `--report connections`

Print a structural connection report instead of diagnostics.

```bash
verilinter --report connections tests/data
```

This report includes:
- parent module to child module instance relationships
- instance names
- port wiring summaries
- wildcard / ordered style notes
- unconnected ports
- duplicate named port bindings
- mixed named and ordered bindings
- unknown child port names
- width mismatch and width-unknown notes
- unread instance-output hints

Design note:
- module / connection diagnostics already run during ordinary linting; `--report connections` is only an alternate structural report view over the same shared analysis, not a separate checker that users must remember to enable

### `--store PATH`

Use a local SQLite analysis store.

```bash
verilinter --store .verilinter.sqlite tests/data
```

When a store is enabled, Verilinter:
- caches reusable per-file worker results
- records each run's diagnostics
- records module / instantiation / connection summaries

### `--no-cache`

Disable cache reuse while still writing the current run to the local SQLite store.

```bash
verilinter --store .verilinter.sqlite --no-cache tests/data
```

### Store Maintenance Subcommands

Verilinter provides dedicated subcommands under `verilinter store` to inspect and maintain SQLite caches:

#### `verilinter store status`

Display cache metrics, recorded run counts, and database file size in JSON format.

```bash
verilinter store status --store .verilinter.sqlite
```

#### `verilinter store prune --days N`

Delete cached per-file analysis results older than `N` days.

```bash
verilinter store prune --days 30 --store .verilinter.sqlite
```

#### `verilinter store prune-runs --keep N`

Keep only the `N` most recently recorded analysis runs and delete older historical runs.

```bash
verilinter store prune-runs --keep 100 --store .verilinter.sqlite
```

#### `verilinter store vacuum`

Reclaim unused SQLite disk space after pruning without removing remaining records.

```bash
verilinter store vacuum --store .verilinter.sqlite
```

#### Legacy Maintenance Flags

For backward compatibility, the following top-level flags remain supported on `verilinter`:
- `--prune-cache-days N`
- `--prune-runs-keep N`
- `--vacuum-store`

## Output Modes

### Text Output

Default diagnostic format:

```text
path/to/file.sv:12:7 - [RULE_CODE] [WARNING] Message text
```

### JSON Output

Useful for scripts and tooling:

```bash
verilinter --format json tests/data
```

### SARIF Output

Useful for CI systems, code scanning, or editor integrations:

```bash
verilinter --format sarif tests/data
```

### Parser and Syntax Errors

When an input file contains syntax errors or invalid Verilog/SystemVerilog constructs that prevent pyslang from forming a valid AST:
- Verilinter emits `PARSER_ERROR` diagnostics with severity `error` and category `syntax_and_structure`.
- AST walking is immediately suppressed for the affected file, preventing spurious downstream lint warnings caused by partial recovery.
- `PARSER_ERROR` diagnostics include the exact file path, line number, column, and the parser's descriptive error message.
- The CLI exits with non-zero failure status (`1`).

## Configuration File

Verilinter supports TOML configuration.

Example:

```toml
[verilinter]
profile = "rtl_strict"
format = "json"
jobs = 4
rules = ["NO_SELF_ASSIGNMENT", "NO_MULTIPLE_NONBLOCKING_WRITES"]
categories = ["rtl_correctness"]
baseline = ".verilinter-baseline.json"

[verilinter.severity]
NO_SELF_ASSIGNMENT = "error"
NO_DUPLICATE_CASE_ITEM = "warning"
```

Supported config fields:
- `profile`
- `format`
- `output`
- `jobs`
- `rules`
- `categories`
- `defines`
- `baseline`
- `severity`
- `store`
- `cache`
- `fail_on_error`
- `fail_on_warning`
- `exit_zero`

CLI options override config-file values.

## Baseline Workflow

Create a baseline:

```bash
verilinter --write-baseline .verilinter-baseline.json tests/data
```

Use the baseline to suppress known findings:

```bash
verilinter --baseline .verilinter-baseline.json tests/data
```

## Connection Report Workflow

Generate a module/port wiring summary:

```bash
verilinter --report connections tests/data
```

This is useful when you want to inspect:
- which modules instantiate which other modules
- how ports are connected
- where ports are left open
- whether named bindings target real child-module ports
- whether width inference found a mismatch or could not infer safely

## Rule Selection Notes

Rule filtering supports three common patterns:

Filter by built-in profile:

```bash
verilinter --profile sv_rtl_subset tests/data
```

Filter by explicit rule codes:

```bash
verilinter --rule NO_UNCONNECTED_INSTANCE_PORTS --rule PORT_CONNECTION_WIDTH_MISMATCH tests/data
```

Filter by category:

```bash
verilinter --category module_correctness tests/data
verilinter --category module_style tests/data
```

## Exit Behavior

- **Default:** returns `0` on successful execution when only lint warnings or errors are found; returns `1` when syntax or parser errors are detected in input files (`PARSER_ERROR` diagnostics are emitted, corrupt AST traversal is suppressed)
- **`--fail-on-error`:** returns `1` if any unsuppressed diagnostics have `error` severity or if parser errors occur
- **`--fail-on-warning`:** returns `1` if any unsuppressed diagnostics have `warning` or `error` severity or if parser errors occur
- **`--exit-zero`:** forces return code `0` even if rule violations or parser errors exist
- returns `1` on CLI/config/input errors such as:
  - missing files or invalid paths
  - invalid config values
  - invalid `--severity` values
  - no `.v` or `.sv` files found
  - attempting to `--write-baseline` when any input file has syntax errors

## Related Docs

- [README.md](../README.md)
- [RULES.md](RULES.md)
- [RULE_IMPLEMENTATION.md](RULE_IMPLEMENTATION.md)
- [STORAGE.md](STORAGE.md)
