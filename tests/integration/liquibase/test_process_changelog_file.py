"""
Integration tests for process_changelog_file against real fixture changelogs in tests/db/.
"""

from __future__ import annotations

# Pytest injects fixtures by the same name as test parameters.
# pylint: disable=redefined-outer-name

from pathlib import Path

import pytest

from liquisketch.liquibase import process_changelog_file
from liquisketch.schema import DatabaseSchema

# tests/integration/liquibase -> tests
_DB_DIR = Path(__file__).resolve().parents[2] / "db"
_FIXTURE_01 = _DB_DIR / "01-initial-schema.xml"
_FIXTURE_02 = _DB_DIR / "02-orders-and-lines.xml"
_FIXTURE_03 = _DB_DIR / "03-drop-legacy-and-order-lines.xml"


def _table_names(model: DatabaseSchema) -> set[str]:
    """Set of table names in ``model``."""
    return {t.name for t in model.tables}


def _fk_outgoing(model: DatabaseSchema) -> set[tuple[str, str, str, str, str]]:
    """Outgoing FK rows as (name, src_table, src_col, tgt_table, tgt_col)."""
    rows: set[tuple[str, str, str, str, str]] = set()
    for t in model.tables:
        for fk in t.foreign_keys:
            rows.add(
                (fk.name, fk.source_table, fk.source_column, fk.target_table, fk.target_column)
            )
    return rows


def _column_names(model: DatabaseSchema, table: str) -> set[str]:
    """Column names for ``table`` in ``model``."""
    for t in model.tables:
        if t.name == table:
            return {c.name for c in t.columns}
    raise AssertionError(f"Table not found: {table}")


@pytest.fixture
def empty_database_schema() -> DatabaseSchema:
    """Fresh schema for a single integration test."""
    return DatabaseSchema(name="integration")


def test_process_01_initial_schema_only(empty_database_schema: DatabaseSchema) -> None:
    """After 01, expect users, deprecated_webhooks, profiles and their FKs."""
    process_changelog_file(empty_database_schema, _FIXTURE_01)

    assert _table_names(empty_database_schema) == {"users", "deprecated_webhooks", "profiles"}

    assert _column_names(empty_database_schema, "users") == {"id", "email"}
    assert _column_names(empty_database_schema, "deprecated_webhooks") == {
        "id",
        "user_id",
        "callback_url",
    }
    assert _column_names(empty_database_schema, "profiles") == {"id", "user_id", "display_name"}

    assert _fk_outgoing(empty_database_schema) == {
        (
            "fk_deprecated_webhooks_user",
            "deprecated_webhooks",
            "user_id",
            "users",
            "id",
        ),
        ("fk_profiles_user", "profiles", "user_id", "users", "id"),
    }


def test_process_01_then_02_orders_and_lines(empty_database_schema: DatabaseSchema) -> None:
    """After 01 + 02, expect order tables and all FKs from fixtures."""
    process_changelog_file(empty_database_schema, _FIXTURE_01)
    process_changelog_file(empty_database_schema, _FIXTURE_02)

    assert _table_names(empty_database_schema) == {
        "users",
        "deprecated_webhooks",
        "profiles",
        "orders",
        "order_lines",
    }

    assert _column_names(empty_database_schema, "orders") == {"id", "user_id", "placed_at"}
    assert _column_names(empty_database_schema, "order_lines") == {"id", "order_id", "sku", "quantity"}

    assert _fk_outgoing(empty_database_schema) == {
        (
            "fk_deprecated_webhooks_user",
            "deprecated_webhooks",
            "user_id",
            "users",
            "id",
        ),
        ("fk_profiles_user", "profiles", "user_id", "users", "id"),
        ("fk_orders_user", "orders", "user_id", "users", "id"),
        ("fk_order_lines_order", "order_lines", "order_id", "orders", "id"),
    }


def test_process_01_02_then_03_drops_legacy_and_order_lines(
    empty_database_schema: DatabaseSchema,
) -> None:
    """After 01 + 02 + 03, legacy and order_lines are removed from the model."""
    process_changelog_file(empty_database_schema, _FIXTURE_01)
    process_changelog_file(empty_database_schema, _FIXTURE_02)
    process_changelog_file(empty_database_schema, _FIXTURE_03)

    assert _table_names(empty_database_schema) == {"users", "profiles", "orders"}

    assert _fk_outgoing(empty_database_schema) == {
        ("fk_profiles_user", "profiles", "user_id", "users", "id"),
        ("fk_orders_user", "orders", "user_id", "users", "id"),
    }
