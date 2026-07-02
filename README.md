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
- Undeclared variables.
- Unused variables.
- Redeclared variables.
- Default case in a case statement.
- Duplicate module definitions across files.
- Instantiation of a module that isn't defined anywhere in the linted files.

More rules coming in the future.

## Try It Out
### Go to the root directory in terminal and type: 

```python src/run_lint.py <file.v> ``` 

or

```python src/run_lint.py <file.sv> ```

Example (single file): 
```python src/run_lint.py tests/data/simple.v```

Example (multiple files, or a directory):
```python src/run_lint.py tests/data/dup_module_a.v tests/data/dup_module_b.v```

### Test it with pytest:

```python -m pytest```

