"""
Unit tests for liquisketch.liquibase.changelog_file.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from liquisketch.liquibase.changelog_file import process_changelog_file
from liquisketch.liquibase.exceptions import LiquibaseReadingError
from liquisketch.schema import DatabaseSchema


def test_process_changelog_file_rejects_non_database_changelog_root(tmp_path: Path) -> None:
    """Non-``databaseChangeLog`` roots raise :exc:`LiquibaseReadingError`."""
    bad = tmp_path / "bad.xml"
    bad.write_text('<?xml version="1.0"?><notDatabaseChangeLog/>', encoding="utf-8")
    schema = DatabaseSchema(name="x")
    with pytest.raises(LiquibaseReadingError, match="Expected databaseChangeLog"):
        process_changelog_file(schema, bad)


def test_process_changelog_file_applies_change_set_from_file(tmp_path: Path) -> None:
    """A minimal changelog file applies ``createTable`` into the schema."""
    changelog = tmp_path / "fragment.xml"
    changelog.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog">\n'
        '  <changeSet id="one" author="unit">\n'
        '    <createTable tableName="solo">\n'
        '      <column name="id" type="BIGINT">'
        '<constraints primaryKey="true" nullable="false"/></column>\n'
        "    </createTable>\n"
        "  </changeSet>\n"
        "</databaseChangeLog>\n",
        encoding="utf-8",
    )
    schema = DatabaseSchema(name="solo-db")
    process_changelog_file(schema, changelog)
    assert len(schema.tables) == 1
    assert schema.tables[0].name == "solo"
