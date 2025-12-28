from impl import TinyLRU


def test_set_get():
    cache = TinyLRU(maxsize=2)
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.get("a") == 1
    assert cache.get("b") == 2


def test_eviction():
    cache = TinyLRU(maxsize=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    assert cache.get("a") is None
    assert len(cache) == 2

# TODO: add tests for update and access order.
