from rugged.unflatteners import parse_key


def test_find_square_bracket_pairs() -> None:
    assert parse_key("contacts[name]") == ("contacts", ["name"])
    assert parse_key("results[0][name]") == ("results", ["0", "name"])
    assert parse_key("created_at") == ("created_at", [])


def test_find_empty_square_bracket_pairs() -> None:
    assert parse_key("contacts[]") == ("contacts", [None])


def test_broken_brackets() -> None:
    assert parse_key("address[road") == ("address[road", [])
    assert parse_key("address]city[") == ("address]city[", [])
    assert parse_key("[address][postcode]") == (None, ["address", "postcode"])
