import copy
from collections.abc import Mapping
import re
from typing import Any, Iterable, TypeVar

key_pattern = re.compile(r"\[([^\]]*)\]")

ParsedKey = tuple[str | None, list[str | None]]
ValidParsedKey = tuple[str, list[str | None]]


def parse_key(key: str) -> ParsedKey:
    """
    Finds paired square brackets in a key, and returns the inner values

    For example, results[0][name] will return 'results', ['0', 'name']

    When no bracket pairs are present, an empty list is returned.

    Empty square brackets, to represent auto-numbering of list indices, are represented as None

    When no root key is given (e.g. [0][name]), the root key will be None.

    """

    key_pairs = key_pattern.findall(key)

    # If there was a matched key, use the text before as the prefix
    prefix: str | None = key
    if len(key_pairs) > 0:
        prefix = key.split(f"[{key_pairs[0]}]", 1)[0]
    prefix = prefix if prefix else None

    return prefix, [sub_key if len(sub_key) > 0 else None for sub_key in key_pairs]


def unflatten(data: dict[str, Any]) -> dict[str, Any] | list[Any]:
    """
    Unflatten a flat dictionary into a nested dictionary

    The input dictionary is expected to be as received by a HTTP client. i.e.:
    - Ordered
    - Flat
    - Duplicate keys as one key with a list of values

    We follow these rules:

    1. Keys without square brackets are returned straightforwardly:

    => { "action": "signup", "email": "foo@example.com" }
    <= { "action": "signup", "email": "foo@example.com" }

    2. Keys with named square brackets are treated as objects:

    => { "address[zipcode]": "90210" }
    <= { "address": { "zipcode": "90210" } }

    3. Keys with postfix empty square brackets are treated as lists:

    => { "emails[]": ["foo@example.com", "bar@example.com"] }
    <= { "emails": ["foo@example.com", "bar@example.com"] }

    4. Keys with prefix empty square brackets are treated as lists of objects:

    => { "users[][id]": [1, 2], "users[][name]": ["foo", "bar"] }
    <= { "users": [{ "id": 1, "name": "foo" }, { "id": 2, "name": "bar" }] }

    5. TODO: Currently, keys with numbered square brackets are treated as rule 2, but will be treated more like rule 4 in future.

    6. Any keys that do not conform to these rules are returned as-is.

    For clarity, in this function we use the following terminology:
    - the "root key" is the key before the first square bracket
    - "indexes" are the values inside the square brackets
        - A None index is used as a marker for a list
    - a "path" is an address to a nested value, including the root key and indexes, e.g. users[][name] => ("users", None, "name")

    """

    # The nested dictionary we're building
    nested: dict[str, Any] = {}

    # A list of paths
    list_paths: list[tuple[str]] = []

    for key, value in data.items():
        # Get the root key (before square brackets) and indices
        root_key, indexes = parse_key(key)

        # Return invalid keys like `[address][postcode]` as-is
        # TODO: boot these out in parse_keys
        if root_key is None:
            nested[key] = value
            continue

        # root is used as a reference to the part of the nested dictionary we're building
        root = nested
        # Marks when we have replaced root with a list
        root_is_list = False

        # Simple key => value items
        if len(indexes) == 0:
            root[root_key] = value
            continue

        # Set root
        if root_key not in root:
            root[root_key] = {}

        # parent is used to replace a root with a list later on
        parent = root
        root = root[root_key]

        for idx, index in enumerate(indexes):
            # Setup some contextual vars
            prev_idx = indexes[idx - 1] if idx > 0 else root_key
            is_last = idx == len(indexes) - 1
            path = (root_key, *indexes[: idx + 1])
            is_list = index is None

            # Empty-square-bracket cases, item[] => value
            if is_list:
                # Replace previous item with a list
                # TODO: If root was set to a value/map earlier, this will overwrite root. Unsure how to handle - error?
                if not isinstance(root, list):
                    root = parent
                    assert prev_idx is not None
                    root[prev_idx] = []
                    # Capture path for restructuring later
                    list_paths.append(path[:-1])  # type: ignore[arg-type]

                # Don't change parent as we've replaced it
                root = parent[prev_idx]
                root_is_list = True

                # Handle root_key[...][] = value
                if is_last:
                    assert isinstance(root, list) and root_is_list
                    root.extend(value) if isinstance(value, list) else root.append(
                        value
                    )

                continue

            assert index is not None

            # Named square-bracket cases, item[...][key] => value
            if root_is_list and is_last:
                # Create mapping to append to list
                obj = {}

                # Wrap item in a list here, for consistency when restructuring
                if not isinstance(value, list):
                    value = [value]

                obj[index] = value
                assert isinstance(root, list) and root_is_list
                root.append(obj)

                continue

            # Create a new map
            if index not in root:
                root[index] = {}

            # Use the map going forward
            if not is_last:
                parent = root
                root = root[index]
                continue

            # Set the map value, item[key] = value
            root[index] = value

    # Restructure lists of objects into multiple objects
    for path in list_paths:
        # Get the list of objects from the nested dictionary
        nested_root: dict[str, Any] = nested
        target: list[dict[str, Any]]
        # Container is the object that contains this list, and the key it is set to
        # TODO: This probably doesn't work with root[][][key] paths (but should it?)
        container: dict[str, Any] = {}
        container_key: str = ""
        for idx, part in enumerate(path):
            # Capture container
            if idx == len(path) - 1:
                container = nested_root
                container_key = part
            nested_root = nested_root[part]

        if not isinstance(nested_root, list):
            # TODO: Raise warning
            continue

        target = nested_root

        # Restructure the list into a list of objects
        container[container_key] = restructure_list(target)

    # Post-process the data to convert sequential 0-indexed integer keys to list
    nested = sequential_keys_to_list(nested)

    return nested


def sequential_keys_to_list(data: dict[str, Any]) -> dict[str, Any]:
    """
    Processes the dict to convert:
        {
            "users": {
                "0": { "name": "Foo" },
                "1": { "name": "Bar" },
            },
            "user_aliases": {
                "by_idx": {
                    "0": "Foo",
                    "1": "Bar",
                },
            },
        }
    to
        {
            "users": [
                { "name": "Foo" },
                { "name": "Bar" },
            ],
            "user_aliases": {
                "by_idx": [
                    "Foo",
                    "Bar",
                ],
            },
        }

    """

    def walk(node_: Any) -> Any:
        node = copy.copy(node_)

        if isinstance(node, dict):
            # If all keys are 0-indexed, sequential integers, convert to list
            is_digits = all(k.isdigit() for k in node.keys())
            is_0_indexed = len(node.keys()) and list(node.keys())[0] == "0"
            is_sequential = list(node.keys()) == list(map(str, range(len(node.keys()))))

            if all([is_digits, is_0_indexed, is_sequential]):
                return list(walk(list(node.values())))

            for k, v in node.items():
                node[k] = walk(v)

            return node

        if isinstance(node, list):
            return [walk(v) for v in node]

        return node

    result = walk(data)
    assert isinstance(result, dict)
    return result


def restructure_list(target: list[Any]) -> list[dict[str, Any]]:
    # If this is a list of scalar values, we don't need to restructure
    if not all(isinstance(obj, Mapping) for obj in target):
        return target

    # Each obj in target will be an map with one key and a list of values

    # Compose each obj into a single map
    # Duplicates are supported, but shouldn't be common
    key_values: dict[str, list[str]] = {}
    for obj in target:
        for key, value in obj.items():
            if key not in key_values:
                key_values[key] = []
            key_values[key].extend(value)

    # Sanity check that all lists are the same length
    # TODO: Raise error?
    assert all_equal(
        [len(values) for values in key_values.values()]
    ), "objects in list have mismatching item counts"

    # Get the number of resulting objects
    item_count = len(list(key_values.values())[0])

    # Create a new object with its associated keys
    objs = []
    for idx in range(item_count):
        obj = {}
        for key, values in key_values.items():
            obj[key] = values[idx]
        objs.append(obj)

    return objs


T = TypeVar("T")


def all_equal(items: Iterable[T]) -> bool:
    val: T | None = None
    for item in items:
        if val is None:
            val = item
            continue

        if val != item:
            return False

    return True
