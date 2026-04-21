"""
Liquibase changelog reading: build a :class:`~liquisketch.schema.DatabaseSchema` from XML.

Flow:

1. :func:`load_database_schema_from_master_changelog` — start from ``changelog-master.xml``.
2. :func:`process_changelog_file` — one file, includes + change sets.
3. :func:`apply_changeset_to_schema` — apply one change set to the model.
"""

from __future__ import annotations

from .changeset_apply import apply_changeset_to_schema
from .changelog_file import process_changelog_file
from .exceptions import LiquibaseReadingError
from .master_changelog import load_database_schema_from_master_changelog
from .types import ChangeSetRef

__all__ = [
    "ChangeSetRef",
    "LiquibaseReadingError",
    "apply_changeset_to_schema",
    "load_database_schema_from_master_changelog",
    "process_changelog_file",
]
