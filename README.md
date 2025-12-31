# Verilinter

A static analysis framework for SystemVerilog, using pyslang. Pyslang parses source code into an AST. The framework walks the tree, builds semantic context (symbol table, scopes, symbols), and applies linting rules over the structure.

## Features
- Tracks lexical scopes (modules, blocks, always blocks, etc.)
- Tracks symbols (variables, signals, ports)
- Supports rule-based analysis (lint-style checks)

## Rules Implemented
A basic set of rules are implemented. Right now, it checks for: 
- Non-blocking assignments in combinational logic.
- Blocking assignments in sequential logic.
- Undeclared variables.
- Unused variables.
- Default case in a case statement.

More rules coming in the future.

## Try It Out
### Go to the root directory in terminal and type: 

```python run_lint.py <file.v> ``` 

or

```python run_lint.py <file.sv> ```

Example: 
```python run_lint.py tests/data/simple.v```

### Testing with pytest: 

```python -m pytest```

### Testing without pytest:

```python -m file_name```

