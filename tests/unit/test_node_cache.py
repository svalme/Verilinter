from src.pkg.parser._syntax_queries.node_cache import MISSING, node_cache_get, node_cache_put


class _Node:
    pass


def test_hit_returns_value_for_the_same_node() -> None:
    cache: dict[object, object] = {}
    node = _Node()
    node_cache_put(cache, "tag", node, 42)
    assert node_cache_get(cache, "tag", node) == 42


def test_cached_none_is_distinguished_from_a_miss() -> None:
    cache: dict[object, object] = {}
    node = _Node()
    node_cache_put(cache, "tag", node, None)
    assert node_cache_get(cache, "tag", node) is None
    assert node_cache_get(cache, "tag", _Node()) is MISSING


def test_entry_whose_node_differs_is_a_miss_even_with_a_colliding_key() -> None:
    cache: dict[object, object] = {}
    stored, queried = _Node(), _Node()
    cache[("tag", id(queried))] = (stored, "stale")  # what a recycled id would look like
    assert node_cache_get(cache, "tag", queried) is MISSING


def test_entry_keeps_its_node_alive_so_the_id_cannot_be_recycled() -> None:
    import sys

    cache: dict[object, object] = {}
    node = _Node()
    before = sys.getrefcount(node)
    node_cache_put(cache, "tag", node, 1)
    assert sys.getrefcount(node) > before


def test_tags_are_independent_and_missing_cache_is_a_miss() -> None:
    cache: dict[object, object] = {}
    node = _Node()
    node_cache_put(cache, "a", node, 1)
    assert node_cache_get(cache, "b", node) is MISSING
    assert node_cache_get(None, "a", node) is MISSING
    node_cache_put(None, "a", node, 1)


def test_memoized_node_query_decorator() -> None:
    from src.pkg.parser._syntax_queries.node_cache import memoized_node_query

    call_count = 0

    @memoized_node_query(tag="test_query", node_arg=0, ctx_arg=1)
    def compute(node: object, ctx: object = None) -> int:
        nonlocal call_count
        call_count += 1
        return 99

    node = _Node()
    cache: dict[object, object] = {}

    # Call with direct cache dict as ctx
    assert compute(node, cache) == 99
    assert call_count == 1

    # Second call hits cache
    assert compute(node, cache) == 99
    assert call_count == 1

    # Different node triggers new call
    other_node = _Node()
    assert compute(other_node, cache) == 99
    assert call_count == 2

    # Without cache, runs function directly without crashing
    assert compute(node, None) == 99
    assert call_count == 3


def test_memoized_node_query_extracts_from_context_object() -> None:
    from src.pkg.parser._syntax_queries.node_cache import memoized_node_query

    class MockContext:
        def __init__(self) -> None:
            self.data = {"module_cache": {}}

    call_count = 0

    @memoized_node_query(tag="query_tag", node_arg="raw_node", ctx_arg="ctx")
    def inspect_node(raw_node: object, ctx: object) -> str:
        nonlocal call_count
        call_count += 1
        return "result"

    ctx = MockContext()
    node = _Node()

    assert inspect_node(raw_node=node, ctx=ctx) == "result"
    assert call_count == 1
    assert inspect_node(raw_node=node, ctx=ctx) == "result"
    assert call_count == 1


def test_memoized_node_query_unwraps_vnode_raw() -> None:
    from src.pkg.parser._syntax_queries.node_cache import memoized_node_query

    raw_node = _Node()

    class FakeVNode:
        raw = raw_node

    cache: dict[object, object] = {}
    calls = 0

    @memoized_node_query(tag="vnode_tag")
    def get_val(node: object, cache: object = None) -> str:
        nonlocal calls
        calls += 1
        return "ok"

    vnode = FakeVNode()
    assert get_val(vnode, cache=cache) == "ok"
    assert calls == 1

    # Calling with the raw node itself also hits the exact same cache entry
    assert get_val(raw_node, cache=cache) == "ok"
    assert calls == 1

