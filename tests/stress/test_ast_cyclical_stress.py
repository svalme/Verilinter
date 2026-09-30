"""Cyclical graph and loop immunity stress tests across all AST query functions.

Validates that:
1. Every exported syntax query function safely terminates without hanging,
   infinite loops, or raising RecursionError when subjected to self-referential
   cycles (A -> A) and multi-node cyclic graph topologies (A -> B -> A, A -> B -> C -> A).
2. Traversal generators (e.g. iter_identifier_reads, iter_assignment_nodes) do not
   recurse infinitely when consumed on cyclic child graphs.
3. Expression folding, selector extraction, target resolution, and descendant
   containment queries execute with complete loop immunity.
"""
from __future__ import annotations

import inspect
from unittest.mock import Mock

import pytest
import pyslang as sl

import src.pkg.parser.syntax_queries as sq
from src.pkg.parser.syntax_kinds import (
    ADD_EXPRESSION_KIND,
    BINARY_AND_EXPRESSION_KIND,
    CONCATENATION_EXPRESSION_KIND,
    DIVIDE_EXPRESSION_KIND,
    ELEMENT_SELECT_EXPRESSION_KIND,
    EQUALITY_EXPRESSION_KIND,
    LOGICAL_SHIFT_LEFT_EXPRESSION_KIND,
    MULTIPLE_CONCATENATION_EXPRESSION_KIND,
    MULTIPLY_EXPRESSION_KIND,
    PARENTHESIZED_EXPRESSION_KIND,
    SUBTRACT_EXPRESSION_KIND,
    UNARY_MINUS_EXPRESSION_KIND,
    UNARY_PLUS_EXPRESSION_KIND,
)
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.context import Context
from tests.support.termination import terminates_within


pytestmark = pytest.mark.stress


def _build_cyclic_node(kind: int = 999999) -> Mock:
    """Build a mock SyntaxNode that forms a direct self-referential cycle on all fields."""
    node = Mock(spec=sl.SyntaxNode)
    node.parent = node
    node.left = node
    node.right = node
    node.select = node
    node.expr = node
    node.operand = node
    node.expression = node
    node.concatenation = node
    node.predicate = node
    node.statement = node
    node.clause = node
    node.elseClause = node
    node.block = node
    node.header = node
    node.name = node
    node.type = node
    node.initializer = node
    node.assignments = [node]
    node.expressions = [node]
    node.instances = [node]
    node.parameters = [node]
    node.connections = [node]
    node.items = [node]
    node.members = [node]
    node.conditions = [node]
    node.decls = [node]
    node.kind = kind
    node.__iter__ = lambda self: iter([node])
    return node


def _build_cyclic_ring(length: int = 3, kind: int = 999999) -> list[Mock]:
    """Build a ring of mock SyntaxNodes where each node references the next."""
    nodes = [Mock(spec=sl.SyntaxNode) for _ in range(length)]
    for i, node in enumerate(nodes):
        nxt = nodes[(i + 1) % length]
        node.parent = nxt
        node.left = nxt
        node.right = nxt
        node.select = nxt
        node.expr = nxt
        node.operand = nxt
        node.expression = nxt
        node.concatenation = nxt
        node.predicate = nxt
        node.statement = nxt
        node.clause = nxt
        node.elseClause = nxt
        node.block = nxt
        node.header = nxt
        node.name = nxt
        node.type = nxt
        node.initializer = nxt
        node.assignments = [nxt]
        node.expressions = [nxt]
        node.instances = [nxt]
        node.parameters = [nxt]
        node.connections = [nxt]
        node.items = [nxt]
        node.members = [nxt]
        node.conditions = [nxt]
        node.decls = [nxt]
        node.kind = kind
        node.__iter__ = (lambda target: lambda self: iter([target]))(nxt)
    return nodes


def _get_exported_query_functions() -> list[tuple[str, object]]:
    """Retrieve all exported public callable queries from syntax_queries."""
    funcs = []
    for name in sorted(dir(sq)):
        if name.startswith("_"):
            continue
        obj = getattr(sq, name)
        if callable(obj):
            funcs.append((name, obj))
    return funcs


ALL_QUERY_FUNCTIONS = _get_exported_query_functions()


@pytest.mark.parametrize("name,func", ALL_QUERY_FUNCTIONS, ids=[f[0] for f in ALL_QUERY_FUNCTIONS])
def test_syntax_query_single_node_cycle_immunity(name: str, func: object) -> None:
    """Stress tests every individual syntax query with a self-referential node cycle."""
    cyclic = _build_cyclic_node()

    mock_ctx = Mock()
    mock_ctx.stack = [Mock(raw=cyclic, location={"file": "test.sv", "line": 1, "col": 1})]
    mock_ctx.scope = Mock(return_value=None)
    mock_symtab = Mock()
    mock_tree = Mock(spec=sl.SyntaxTree)
    mock_tree.sourceManager = None
    mock_tree.root = cyclic

    sig = inspect.signature(func)
    args = []
    for param in sig.parameters.values():
        pname = param.name.lower()
        if "ctx" in pname:
            args.append(mock_ctx)
        elif "symbol_table" in pname or "symtab" in pname:
            args.append(mock_symtab)
        elif "scope" in pname:
            args.append(cyclic)
        elif "tree" in pname:
            args.append(mock_tree)
        elif param.default is not inspect.Parameter.empty:
            continue
        else:
            args.append(cyclic)

    with terminates_within(f"{name}"):
        try:
            res = func(*args)
            if inspect.isgenerator(res):
                for _ in zip(range(100), res):
                    pass
        except (TypeError, AttributeError, ValueError):
            # Graceful type/attribute errors from synthetic mock structure are expected
            pass


@pytest.mark.parametrize("name,func", ALL_QUERY_FUNCTIONS, ids=[f[0] for f in ALL_QUERY_FUNCTIONS])
def test_syntax_query_multi_node_cycle_immunity(name: str, func: object) -> None:
    """Stress tests every individual syntax query with a multi-node cyclical ring (A -> B -> C -> A)."""
    ring = _build_cyclic_ring(length=3)
    entry_node = ring[0]

    mock_ctx = Mock()
    mock_ctx.stack = [Mock(raw=entry_node, location={"file": "test.sv", "line": 1, "col": 1})]
    mock_ctx.scope = Mock(return_value=None)
    mock_symtab = Mock()
    mock_tree = Mock(spec=sl.SyntaxTree)
    mock_tree.sourceManager = None
    mock_tree.root = entry_node

    sig = inspect.signature(func)
    args = []
    for param in sig.parameters.values():
        pname = param.name.lower()
        if "ctx" in pname:
            args.append(mock_ctx)
        elif "symbol_table" in pname or "symtab" in pname:
            args.append(mock_symtab)
        elif "scope" in pname:
            args.append(entry_node)
        elif "tree" in pname:
            args.append(mock_tree)
        elif param.default is not inspect.Parameter.empty:
            continue
        else:
            args.append(entry_node)

    with terminates_within(f"{name}"):
        try:
            res = func(*args)
            if inspect.isgenerator(res):
                for _ in zip(range(100), res):
                    pass
        except (TypeError, AttributeError, ValueError):
            pass


def test_evaluate_constant_expression_binary_cycles() -> None:
    """Verifies constant folding terminates immediately on cyclic binary operations."""
    for binary_kind in (
        ADD_EXPRESSION_KIND,
        SUBTRACT_EXPRESSION_KIND,
        MULTIPLY_EXPRESSION_KIND,
        DIVIDE_EXPRESSION_KIND,
        LOGICAL_SHIFT_LEFT_EXPRESSION_KIND,
        BINARY_AND_EXPRESSION_KIND,
        EQUALITY_EXPRESSION_KIND,
    ):
        node = Mock(spec=sl.SyntaxNode)
        node.kind = binary_kind
        node.left = node
        node.right = node

        with terminates_within():
            val = sq.evaluate_constant_expression(node)
            assert val is None


def test_evaluate_constant_expression_unary_cycles() -> None:
    """Verifies constant folding terminates on cyclic unary operations."""
    for unary_kind in (UNARY_PLUS_EXPRESSION_KIND, UNARY_MINUS_EXPRESSION_KIND):
        node = Mock(spec=sl.SyntaxNode)
        node.kind = unary_kind
        node.operand = node

        with terminates_within():
            val = sq.evaluate_constant_expression(node)
            assert val is None


def test_unwrap_parentheses_cycle() -> None:
    """Verifies unwrap_parentheses breaks cycle immediately when parenthesized expression points to self."""
    node = Mock(spec=sl.SyntaxNode)
    node.kind = PARENTHESIZED_EXPRESSION_KIND
    node.expression = node

    with terminates_within():
        res = sq.unwrap_parentheses(node)
        assert res is node


def test_contains_descendant_child_cycle() -> None:
    """Verifies contains_descendant terminates without RecursionError on cyclic child graphs."""
    cyclic = _build_cyclic_node()
    target = Mock(spec=sl.SyntaxNode)

    with terminates_within():
        assert sq.contains_descendant(cyclic, target) is False


def test_generator_traversals_on_child_cycle() -> None:
    """Verifies generator queries pull items safely without hanging when child graph is cyclic."""
    cyclic = _build_cyclic_node()

    # 1. iter_identifier_reads
    with terminates_within():
        reads = list(sq.iter_identifier_reads(cyclic))
        assert isinstance(reads, list)

    # 2. iter_assignment_nodes
    with terminates_within():
        assigns = list(sq.iter_assignment_nodes(cyclic))
        assert isinstance(assigns, list)

    # 3. iter_statement_nodes
    with terminates_within():
        stmts = list(sq.iter_statement_nodes(cyclic))
        assert isinstance(stmts, list)


def test_assignment_target_resolution_cyclical_shapes() -> None:
    """Verifies resolve_assignment_target handles cyclical concats and element selects without recursion error."""
    # 1. Cyclical ElementSelectExpression
    elem_select = Mock(spec=sl.SyntaxNode)
    elem_select.kind = ELEMENT_SELECT_EXPRESSION_KIND
    elem_select.select = elem_select
    elem_select.left = elem_select

    base_name, selectors = sq.extract_assignment_target_and_selectors(elem_select)
    assert base_name is None
    assert isinstance(selectors, list)

    # 2. Cyclical ConcatenationExpression
    concat_node = Mock(spec=sl.SyntaxNode)
    concat_node.kind = CONCATENATION_EXPRESSION_KIND
    concat_node.expressions = [concat_node]

    scope = Mock()
    scope.lookup = Mock(return_value=None)
    scope.lookup_hierarchical = Mock(return_value=None)

    target = sq.resolve_assignment_target(concat_node, scope)
    assert target is None

    # 3. Cyclical MultipleConcatenationExpression
    mult_concat = Mock(spec=sl.SyntaxNode)
    mult_concat.kind = MULTIPLE_CONCATENATION_EXPRESSION_KIND
    mult_concat.expression = mult_concat
    mult_concat.concatenation = mult_concat

    target_mult = sq.resolve_assignment_target(mult_concat, scope)
    assert target_mult is None


def test_state_register_reset_covered_cycle_immunity() -> None:
    """Verifies is_state_register_reset_covered terminates when block children form a cycle."""
    block = _build_cyclic_node()
    block.kind = 999999

    with terminates_within():
        covered = sq.is_state_register_reset_covered(block, "state_reg")
        assert covered is False


def test_has_latch_pattern_deep_and_cyclic_immunity() -> None:
    """Verifies latch pattern analysis terminates cleanly on cyclic and deeply nested statements."""
    from src.pkg.rules.combinational_logic.no_latch_in_always_comb import has_latch_pattern, _analyze_statement_latch

    # 1. Direct cyclic node
    cyclic = _build_cyclic_node()
    with terminates_within():
        has_latch, assigned = _analyze_statement_latch(cyclic, set())
        assert has_latch is False
        assert isinstance(assigned, set)
        assert has_latch_pattern(cyclic) is False

    # 2. Deeply nested block of 300 levels
    from src.pkg.parser.syntax_kinds import BLOCK_STATEMENT_KINDS
    block_kind = next(iter(BLOCK_STATEMENT_KINDS))
    curr = Mock(spec=sl.SyntaxNode)
    curr.kind = block_kind
    curr.statements = ()
    for _ in range(300):
        parent = Mock(spec=sl.SyntaxNode)
        parent.kind = block_kind
        parent.statements = (curr,)
        curr = parent

    with terminates_within():
        has_latch, _ = _analyze_statement_latch(curr, set())
        assert has_latch is False


def test_combinational_loop_deep_signal_graph_immunity() -> None:
    """Verifies combinational loop detection does not exceed call stack on deep signal chains."""
    from src.pkg.rules.combinational_logic.combinational_loop import CombinationalLoopRule

    rule = CombinationalLoopRule()
    # Construct a 500-node linear DAG: sig_0 -> sig_1 -> ... -> sig_499
    graph: dict[str, list[tuple[str, dict[str, Any], tuple[str, ...]]]] = {}
    for i in range(500):
        graph[f"sig_{i}"] = [(f"sig_{i+1}", {"line": 1, "col": 1}, ())]
    graph["sig_500"] = []

    with terminates_within():
        diagnostics = rule._find_cycles(graph)
        assert diagnostics == []


def test_circular_module_instantiation_deep_chain_immunity() -> None:
    """Verifies circular module instantiation DFS bounds depth on deep instantiation hierarchies."""
    from src.pkg.rules.connectivity_and_hierarchy.circular_module_instantiation import CircularModuleInstantiationRule

    rule = CircularModuleInstantiationRule()
    symtab = SymbolTable()
    # 500 module chain
    for i in range(500):
        symtab.instantiation_edges.append((f"mod_{i}", f"mod_{i+1}", {"line": 1, "col": 1}))

    with terminates_within():
        diagnostics = rule.run(symtab)
        assert diagnostics == []


def test_no_assignment_width_mismatch_deep_rhs_selects_immunity() -> None:
    """Verifies _check_selects terminates without RecursionError on cyclic raw nodes."""
    from src.pkg.rules.width_and_signedness.no_assignment_width_mismatch import _check_selects

    cyclic = _build_cyclic_node()
    mock_ctx = Mock()
    mock_scope = Mock()
    mock_scope.lookup = Mock(return_value=None)
    mock_scope.lookup_hierarchical = Mock(return_value=None)

    with terminates_within():
        mismatch = _check_selects(cyclic, mock_scope, mock_ctx, None)
        assert mismatch is None


def test_instance_record_cyclic_generate_signature_immunity() -> None:
    """Verifies InstanceRecord.from_dict terminates on cyclic signature structures."""
    from src.pkg.semantic.models.instance_record import InstanceRecord

    cyclic_list: list[Any] = []
    cyclic_list.append(cyclic_list)

    rec = InstanceRecord.from_dict({
        "parent_module": "top",
        "child_module": "sub",
        "instance_name": "u_sub",
        "generate_branch_signature": cyclic_list,
    })
    assert isinstance(rec.generate_branch_signature, tuple)

