"""
Integration-style tests for loading a composed changelog via the master entrypoint.

Uses the shared fixture under tests/db/.
"""

from __future__ import annotations

# Pytest injects ``master_changelog_path`` into the test parameter of the same name.
# pylint: disable=redefined-outer-name

from pathlib import Path

import pytest

from liquisketch.liquibase import load_database_schema_from_master_changelog


def _fixture_master() -> Path:
    """Path to ``tests/db/changelog-master.xml``."""
    # tests/unit/liquibase -> tests/unit -> tests
    tests_root = Path(__file__).resolve().parents[2]
    return tests_root / "db" / "changelog-master.xml"


@pytest.fixture
def master_changelog_path() -> Path:
    """Resolved path to the composed master changelog fixture, or skip."""
    path = _fixture_master()
    if not path.is_file():
        pytest.skip(f"Fixture changelog missing: {path}")
    return path


def test_load_master_composed_changelog_end_state(master_changelog_path: Path) -> None:
    """``load_database_schema_from_master_changelog`` matches merged fixture state."""
    schema = load_database_schema_from_master_changelog(master_changelog_path)
    assert schema.name == "changelog-master"
    table_names = {t.name for t in schema.tables}
    assert table_names == {"users", "profiles", "orders"}
    fk_names: set[str] = set()
    for t in schema.tables:
        for fk in t.foreign_keys:
            fk_names.add(fk.name)
    assert fk_names == {"fk_profiles_user", "fk_orders_user"}

    users = next(t for t in schema.tables if t.name == "users")
    assert {c.name for c in users.columns} == {"id", "email"}
