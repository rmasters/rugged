import re
from typing import Any


def unflatten(data: dict[str, Any]) -> dict[str, Any] | list[Any]:
    nested = {}

    # Iterate over flat keys
    for key, value in data.items():
        # Find keys with complete square brackets in
        sub_keys = re.findall(r"\[([^\]]+)\]", key)
        # Skip if no sub-keys
        if len(sub_keys) == 0:
            nested[key] = value
            continue

        # Get root key - root_key[sub_key]
        root_key = re.match(r"^([^\[]+)", key)
        if not root_key or not root_key.group(0) or len(root_key.group(0)) == 0:
            # TODO: Raise a warning
            nested[key] = value
            continue

        if root_key.group(0) not in nested:
            nested[root_key.group(0)] = {}

        # Build nesting structure
        root = nested[root_key.group(0)]
        for idx, key in enumerate(sub_keys):
            if key not in root:
                root[key] = {}

            # If last sub-key, set value
            if idx == len(sub_keys) - 1:
                root[key] = value
                break

            # Set new level root
            root = root[key]

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
