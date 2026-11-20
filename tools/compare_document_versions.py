"""Compare already segmented text by stable section IDs."""

import argparse
import json
from pathlib import Path


def _index_sections(sections):
    if not isinstance(sections, list):
        raise ValueError("Each version must be an array of sections.")
    indexed = {}
    for section in sections:
        if not isinstance(section, dict):
            raise ValueError("Each section must be an object.")
        key, value = section.get("id"), section.get("text")
        if not isinstance(key, str) or not key.strip() or not isinstance(value, str):
            raise ValueError("Each section requires a nonempty string ID and string text.")
        if key in indexed:
            raise ValueError("Duplicate section ID in one version.")
        indexed[key] = value
    return indexed


def compare_versions(before, after):
    old, new = _index_sections(before), _index_sections(after)
    changes = []
    for key in dict.fromkeys([*old, *new]):
        if key not in old:
            status = "added"
        elif key not in new:
            status = "removed"
        elif old[key].split() != new[key].split():
            status = "changed"
        else:
            continue
        changes.append({"id": key, "status": status, "before": old.get(key), "after": new.get(key)})
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON with before and after section arrays")
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not {"before", "after"}.issubset(data):
            raise ValueError("Expected an object containing before and after.")
        result = compare_versions(data["before"], data["after"])
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
