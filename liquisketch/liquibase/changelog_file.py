"""
Read one Liquibase XML changelog file: resolve includes and apply each changeSet.
"""

from __future__ import annotations

import logging
from pathlib import Path

from liquisketch.schema import DatabaseSchema

from .changeset_apply import apply_changeset_to_schema, changeset_ref_from_element
from .exceptions import LiquibaseReadingError
from .xmlutil import is_database_changelog, local_name, parse_database_changelog, resolve_include_path

LOG = logging.getLogger(__name__)


def process_changelog_file(schema: DatabaseSchema, changelog_path: Path) -> DatabaseSchema:
    """
    Process ``databaseChangeLog`` in document order: ``<include>`` (recursive) then
    each ``<changeSet>``. Delegates each changeSet to :func:`apply_changeset_to_schema`.

    :param schema: Current model; mutated in place.
    :param changelog_path: Path to an XML file whose root is ``databaseChangeLog``.
    """
    path = changelog_path.expanduser().resolve()
    LOG.debug("Processing changelog file: %s", path)
    root = parse_database_changelog(path)
    if not is_database_changelog(root):
        msg = f"Expected databaseChangeLog root, got: {local_name(root.tag)}"
        raise LiquibaseReadingError(msg)
    changelog_dir = path.parent
    for child in root:
        tag = local_name(child.tag)
        if tag == "include":
            included = resolve_include_path(child, changelog_dir)
            LOG.debug("Resolved include: %s -> %s", path.name, included)
            process_changelog_file(schema, included)
        elif tag == "changeSet":
            ref = changeset_ref_from_element(child)
            LOG.debug(
                "Applying changeSet id=%s author=%s file=%s",
                ref.changeset_id or "<missing>",
                ref.author or "<missing>",
                path.name,
            )
            apply_changeset_to_schema(schema, ref)
        # Other children (property, etc.) are skipped.
    LOG.debug("Finished changelog file: %s", path)
    return schema
