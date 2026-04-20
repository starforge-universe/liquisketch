#!/usr/bin/env python3
"""
Load tests/db/changelog-master.xml and print the resulting DatabaseSchema.

Run from the repository root::

    python scripts/dump_schema_from_master.py

Or::

    PYTHONPATH=. python scripts/dump_schema_from_master.py
"""

from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path
from pprint import pprint

# Repo root: parent of scripts/
_REPO_ROOT = Path(__file__).resolve().parents[1]
_MASTER_CHANGELOG = _REPO_ROOT / "tests" / "db" / "changelog-master.xml"

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from liquisketch.liquibase import load_database_schema_from_master_changelog


def main() -> int:
    if not _MASTER_CHANGELOG.is_file():
        print(f"Changelog not found: {_MASTER_CHANGELOG}", file=sys.stderr)
        return 1

    schema = load_database_schema_from_master_changelog(_MASTER_CHANGELOG)
    print(f"Master changelog: {_MASTER_CHANGELOG}")
    print()
    pprint(asdict(schema))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
