"""Fold registry/*.yaml self-registrations into input_lists.json and emit
explore/github-data/registryCategories.json for the catalog's category view.

This owns the 'registryRepos' key under input_lists.json's github host
entirely: it is rewritten wholesale from registry/ every run, so deleting a
registry/*.yaml file (deregistration) drops that repo on the next run with
no separate removal logic needed. Unlike 'extraRepos' (hand-maintained,
mixed-purpose), 'registryRepos' is exclusively this script's output -- do
not hand-edit it.

Must run before get_cass_projects.py (see .github/workflows/get_cass_projects.yml),
whose wholesale rewrite of ['https://github.com']['repos'] folds
'registryRepos' in alongside 'extraRepos'.
"""

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_DIR = ROOT / "registry"
INPUT_LISTS = ROOT / "_explore" / "input_lists.json"
CATEGORIES_OUT = ROOT / "explore" / "github-data" / "registryCategories.json"

REQUIRED_KEYS = ("repo", "name", "areas")
NON_ENTRY_FILES = {"TEMPLATE.yaml", "policy.yaml"}


def load_entries():
    entries = []
    for path in sorted(REGISTRY_DIR.glob("*.yaml")):
        if path.name in NON_ENTRY_FILES:
            continue
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        missing = [k for k in REQUIRED_KEYS if not data.get(k)]
        if missing:
            sys.exit(f"{path}: missing required field(s): {missing}")
        if "/" not in data["repo"]:
            sys.exit(f"{path}: repo {data['repo']!r} must be 'owner/name'")
        if not isinstance(data["areas"], list) or not data["areas"]:
            sys.exit(f"{path}: areas must be a non-empty list")
        entries.append(data)
    return entries


def main():
    entries = load_entries()

    with open(INPUT_LISTS) as f:
        input_lists = json.load(f)
    input_lists["https://github.com"]["registryRepos"] = sorted(
        {e["repo"] for e in entries}
    )
    with open(INPUT_LISTS, "w") as f:
        json.dump(input_lists, f, indent=4)

    categories = {}
    for entry in entries:
        for area in entry["areas"]:
            categories.setdefault(area, []).append(entry["repo"])

    CATEGORIES_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(CATEGORIES_OUT, "w") as f:
        json.dump({"data": categories}, f, indent=2)

    print(f"Loaded {len(entries)} registry entr{'y' if len(entries) == 1 else 'ies'}.")


if __name__ == "__main__":
    main()
