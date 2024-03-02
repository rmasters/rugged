from rugged.unflatteners import parse_key


def test_find_square_bracket_pairs() -> None:
    assert parse_key("contacts[name]") == ("contacts", ["name"])
    assert parse_key("results[0][name]") == ("results", ["0", "name"])
    assert parse_key("created_at") == ("created_at", [])


def test_find_empty_square_bracket_pairs() -> None:
    assert parse_key("contacts[]") == ("contacts", [None])
