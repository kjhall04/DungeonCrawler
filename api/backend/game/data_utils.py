import json
import re
from functools import lru_cache


@lru_cache(maxsize=None)
def load_json_file(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def resolve_progression_key(data, prefix, level):
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
    available = []

    for key in data:
        match = pattern.match(str(key))
        if match:
            available.append((int(match.group(1)), key))

    if not available:
        raise KeyError(f"No keys found for prefix '{prefix}'")

    available.sort(key=lambda item: item[0])
    for candidate_level, candidate_key in reversed(available):
        if level >= candidate_level:
            return candidate_key

    return available[0][1]
