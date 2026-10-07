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
