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


def test_unflattening_simple_list() -> None:
    d = {
        "emails[]": ["ross@example.com", "yolo@example.com"],
    }

    assert unflatten(d) == {
        "emails": [
            "ross@example.com",
            "yolo@example.com",
        ]
    }


def test_unflattening_single_list_item_flat_structure() -> None:
    d = {
        "attendees[][name]": "Lyle Lanley",
        "attendees[][email]": "onthemap@example.com",
    }

    assert unflatten(d) == {
        "attendees": [
            {
                "name": "Lyle Lanley",
                "email": "onthemap@example.com",
            },
        ],
    }


def test_unflattening_multi_list_item_flat_structure() -> None:
    d = {
        "attendees[][name]": ["Lyle Lanley", "Mr Snrub"],
        "attendees[][email]": ["onthemap@example.com", "spp@example.com"],
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


@pytest.mark.xfail(reason="Requires further refactoring")
def test_unflattening_single_list_item_deep_structure() -> None:
    """
    Example HTML for this case:
        <input name="recipients[][name][title]" value="Mr">
        <input name="recipients[][name][given_name]" value="Ross">
        <input name="recipients[][name][family_name]" value="Masters">

    """

    d = {
        "recipients[][name][title]": "Mr",
        "recipients[][name][given_name]": "Ross",
        "recipients[][name][family_name]": "Masters",
    }

    assert unflatten(d) == {
        "recipients": [
            {
                "name": {
                    "title": "Mr",
                    "given_name": "Ross",
                    "family_name": "Masters",
                },
            },
        ],
    }


@pytest.mark.xfail(reason="Requires further refactoring")
def test_unflattening_multi_list_item_deep_structure() -> None:
    """
    Example HTML for this case:
        <input name="residents[][name][title]" value="Mr">
        <input name="residents[][name][given_name]" value="Homer">
        <input name="residents[][name][family_name]" value="Simpson">
        <input name="residents[][name][title]" value="Mrs">
        <input name="residents[][name][given_name]" value="Marge">
        <input name="residents[][name][family_name]" value="Simpson">

    """

    d = {
        "residents[][name][title]": ["Mr", "Mrs"],
        "residents[][name][given_name]": ["Homer", "Marge"],
        "residents[][name][family_name]": ["Simpson", "Simpson"],
    }

    assert unflatten(d) == {
        "residents": [
            {
                "name": {
                    "title": "Mr",
                    "given_name": "Homer",
                    "family_name": "Simpson",
                },
            },
            {
                "name": {
                    "title": "Mrs",
                    "given_name": "Marge",
                    "family_name": "Simpson",
                },
            },
        ],
    }


def test_sequential_ints_treated_as_lists() -> None:
    d = {
        "users[0][name]": "Foo",
        "users[0][email]": "foo@example.com",
        "users[1][name]": "Bar",
        "users[1][email]": "bar@example.com",
        "users[2][name]": "Baz",
        "users[2][email]": "baz@example.com",
    }

    assert unflatten(d) == {
        "users": [
            {
                "name": "Foo",
                "email": "foo@example.com",
            },
            {
                "name": "Bar",
                "email": "bar@example.com",
            },
            {
                "name": "Baz",
                "email": "baz@example.com",
            },
        ]
    }


def test_non_sequential_ints_treated_as_named_brackets() -> None:
    d = {
        "users[3][name]": "Foo",
        "users[3][email]": "foo@example.com",
        "users[12][name]": "Bar",
        "users[12][email]": "bar@example.com",
        "users[2][name]": "Baz",
        "users[2][email]": "baz@example.com",
    }

    assert unflatten(d) == {
        "users": {
            "3": {
                "name": "Foo",
                "email": "foo@example.com",
            },
            "12": {
                "name": "Bar",
                "email": "bar@example.com",
            },
            "2": {
                "name": "Baz",
                "email": "baz@example.com",
            },
        }
    }
