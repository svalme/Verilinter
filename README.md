# Verilinter

A static analysis framework for SystemVerilog, using pyslang. Pyslang parses source code into an AST. The framework walks the tree, builds semantic context (symbol table, scopes, symbols), and applies linting rules over the structure.

## Features
- Tracks lexical scopes (modules, blocks, always blocks, etc.)
- Tracks symbols (variables, signals, ports)
- Supports rule-based analysis (lint-style checks)
- Lints multiple files or a whole directory in one run, with a shared symbol table across them -- enables cross-file checks (e.g. duplicate module names)

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

See [RULES.md](RULES.md) for the maintained rule catalog and the specific cases each rule covers.

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

You can still run the script directly if you prefer:

```bash
python src/run_lint.py tests/data/simple.v
```

### Test it with pytest:

```bash
python -m pytest
```

