from impl import slugify


def test_basic_slug():
    assert slugify("Hello, World!") == "hello-world"


def test_trims_hyphens():
    assert slugify("---A---") == "a"

# TODO: add tests for max_len behavior and None input.
