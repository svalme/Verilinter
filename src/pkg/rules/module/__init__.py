"""Cross-file, module-level rules -- kept separate from single-file rules
because they need a merged view across the whole linted batch (the module
registry / instantiation references), not just one file's own scopes.
"""
