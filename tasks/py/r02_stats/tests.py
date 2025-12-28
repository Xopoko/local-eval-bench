from impl import basic_stats


def test_basic_stats_odd():
    stats = basic_stats([3, 1, 2, 2])
    assert stats["count"] == 4
    assert stats["min"] == 1.0
    assert stats["max"] == 3.0
    assert stats["median"] == 2.0


def test_empty():
    stats = basic_stats([])
    assert stats["count"] == 0
    assert stats["mean"] is None

# TODO: add tests for mode, even median, and None input.
