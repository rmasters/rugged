from datetime import datetime, UTC
from uuid import uuid4

import pytest

from rugged.unflatteners import unflatten


def test_unflatten_flat_dict() -> None:
    d = {
        "user_id": uuid4(),
        "email": "ross@example.com",
        "name": ["Ross", "Masters"],
        "join_date": datetime.now(UTC),
    }

    assert unflatten(d) == d


def test_unflatten_nested_dict() -> None:
    d = {
        "user_id": uuid4(),
        "comments": [
            {
                "comment_id": uuid4(),
                "message": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            },
            {
                "comment_id": uuid4(),
                "message": "Aliquam vel ex ac erat feugiat bibendum varius eu ipsum.",
            },
        ],
    }

    assert unflatten(d) == d


def test_unflatten_single_level_nesting() -> None:
    d = {
        "email": "ross@example.com",
        "social[twitter]": "rossmasters",
        "social[github]": "rmasters",
    }

    assert unflatten(d) == {
        "email": "ross@example.com",
        "social": {
            "twitter": "rossmasters",
            "github": "rmasters",
        },
    }


def test_unflatten_broken_brackets() -> None:
    d = {
        "address[road": "main st",
        "address]city[": "london",
        "[address][postcode]": "sw1a 1aa",
    }

    assert unflatten(d) == {
        "address[road": "main st",
        "address]city[": "london",
        # tbd: should this be '[address]': { 'postcode': 'sw1a 1aa' },
        # or even 'address': { 'postcode': 'sw1a 1aa' }}
        "[address][postcode]": "sw1a 1aa",
    }


def test_unflatten_deep_nesting() -> None:
    d = {
        "reports[daily][name]": "Daily report",
        "reports[daily][recipient]": "ross@example.com",
        "reports[daily][schedule]": "0 0 * * *",
        "reports[weekly][name]": "Weekly summary",
        "reports[weekly][recipient]": "ross@example.com",
        "reports[weekly][schedule]": "0 0 0 * *",
        "updated_at": datetime.now(UTC),
    }

    assert unflatten(d) == {
        "reports": {
            "daily": {
                "name": "Daily report",
                "recipient": "ross@example.com",
                "schedule": "0 0 * * *",
            },
            "weekly": {
                "name": "Weekly summary",
                "recipient": "ross@example.com",
                "schedule": "0 0 0 * *",
            },
        },
        "updated_at": d["updated_at"],
    }


def test_unflattening_with_sequential_ints() -> None:
    d = {
        "attendees[0]": "ross@example.com",
        "attendees[1]": "roos@example.com",
        "attendees[2]": "mr.snrub@example.com",
    }

    assert unflatten(d) == {
        "attendees": [
            "ross@example.com",
            "roos@example.com",
            "mr.snrub@example.com",
        ],
    }


def test_unflattening_list_of_dicts() -> None:
    d = {
        "attendees[0][name]": "Lyle Lanley",
        "attendees[0][email]": "onthemap@example.com",
        "attendees[1][name]": "Mr Snrub",
        "attendees[1][email]": "spp@example.com",
    }

    assert unflatten(d) == {
        "attendees": [
            {
                "name": "Lyle Lanley",
                "email": "onthemap@example.com",
            },
            {
                "name": "Mr Snrub",
                "email": "spp@example.com",
            },
        ],
    }


def test_unflattening_mix_keys_and_integer_list() -> None:
    d = {
        "attendees[0]": "Ross",
        "attendees[one]": "Homer",
    }

    assert unflatten(d) == {
        "attendees": {
            "0": "Ross",
            "one": "Homer",
        }
    }


@pytest.mark.xfail(reason="Not yet implemented")
def test_unflattening_list_with_empty_keys() -> None:
    d = [
        ("products[]", "Fish Tacos"),
        ("products[]", "Swan Soufle"),
        ("products[]", "Crayon Croutons"),
    ]

    assert unflatten(d) == {  # type: ignore[arg-type]
        "products": [
            "Fish Tacos",
            "Swan Soufle",
            "Crayon Croutons",
        ],
    }
