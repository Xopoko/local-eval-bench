from impl import parse_pairs


def test_basic_parse():
    assert parse_pairs("a=1; b=two; c=") == {"a": "1", "b": "two", "c": ""}


def test_ignores_empty():
    assert parse_pairs(" ; x=1;; ") == {"x": "1"}

# TODO: add tests for custom separators and missing values.
