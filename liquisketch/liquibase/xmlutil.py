"""
Small helpers for Liquibase XML (namespaces, parsing).
"""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from .exceptions import LiquibaseReadingError


def local_name(tag: str) -> str:
    """Return the local part of a Clark-notation XML tag."""
    if "}" in tag:
        return tag.rsplit("}", maxsplit=1)[-1]
    return tag


def parse_database_changelog(path: Path) -> ET.Element:
    """
    Parse an XML file and return the root element (expected: databaseChangeLog).
    """
    tree = ET.parse(path)
    return tree.getroot()


def is_database_changelog(root: ET.Element) -> bool:
    """Return True if ``root`` is a Liquibase ``databaseChangeLog`` element."""
    return local_name(root.tag) == "databaseChangeLog"


def resolve_include_path(
    include_el: ET.Element,
    changelog_dir: Path,
) -> Path:
    """
    Resolve the file= attribute of an <include> relative to the including file.
    """
    rel = include_el.get("file")
    if not rel:
        msg = "<include> missing file attribute"
        raise LiquibaseReadingError(msg)
    rel_to = include_el.get("relativeToChangelogFile", "false").lower()
    base = changelog_dir if rel_to in ("true", "1", "yes") else Path.cwd()
    return (base / rel).resolve()
