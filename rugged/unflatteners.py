import re
from typing import Any


prefix_pattern = re.compile(r"^([^\[]+)")
key_pattern = re.compile(r"\[([^\]]*)\]")


def parse_key(key: str) -> tuple[str | None, list[str | None]]:
    """
    Finds paired square brackets in a key, and returns the inner values

    For example, results[0][name] will return 'results', ['0', 'name']

    No bracket pairs will be returned as an empty list.

    Empty square brackets, to represent auto-numbering of list indices, are represented as None

    When no root key is given (e.g. [0][name]), the root key will be None.

    """

    prefix_match = prefix_pattern.match(key)
    prefix = None if prefix_match is None else prefix_match.group(0)

    key_pairs = key_pattern.findall(key)
    return prefix, [sub_key if len(sub_key) > 0 else None for sub_key in key_pairs]


def unflatten(data: dict[str, Any]) -> dict[str, Any] | list[Any]:
    nested = {}

    # Iterate over flat keys
    for key, value in data.items():
        # Find keys with complete square brackets in
        root_key, sub_keys = parse_key(key)
        # Skip if no sub-keys
        if len(sub_keys) == 0:
            nested[key] = value
            continue

        # Get root key - root_key[sub_key]
        if not root_key:
            # If root key is empty, return the whole key as-is
            # TODO: Raise a warning
            nested[key] = value
            continue

        if root_key not in nested:
            nested[root_key] = {}

        # Build nesting structure
        root = nested[root_key]
        for idx, sub_key in enumerate(sub_keys):
            if sub_key not in root:
                root[sub_key] = {}

            # If last sub-key, set value
            if idx == len(sub_keys) - 1:
                root[sub_key] = value
                break

            # Set new level root
            root = root[sub_key]

    # Re-process keys, if all are numeric and sequential 0..n, convert to list
    return sequential_numeric_keys_to_lists(nested)


def sequential_numeric_keys_to_lists(
    data: dict[str, Any],
) -> dict[str, Any] | list[Any]:
    if isinstance(data, dict):
        # Check if all keys are sequential numeric
        keys = sorted(data.keys())
        if keys == list(map(str, range(len(keys)))):
            # Restructure to list
            return [sequential_numeric_keys_to_lists(data[key]) for key in keys]
        else:
            # Process nested dicts
            return {key: sequential_numeric_keys_to_lists(data[key]) for key in data}
    else:
        return data
