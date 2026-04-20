"""
Load a :class:`~liquisketch.schema.DatabaseSchema` from a Liquibase master changelog path.
"""

from __future__ import annotations

from pathlib import Path

from liquisketch.schema import DatabaseSchema

from .changelog_file import process_changelog_file


def load_database_schema_from_master_changelog(master_changelog_path: Path) -> DatabaseSchema:
    """
    Build a schema by processing ``changelog_path`` (typically ``changelog-master.xml``),
    following ``<include>`` elements in order and applying every ``<changeSet>``.

    This creates an empty :class:`~liquisketch.schema.DatabaseSchema` and runs
    :func:`~liquisketch.liquibase.changelog_file.process_changelog_file` on the master file,
    which recursively processes included fragments.
    """
    master_path = master_changelog_path.expanduser().resolve()
    schema = DatabaseSchema(name=master_path.stem)
    process_changelog_file(schema, master_path)
    return schema
