"""
Unit tests for liquisketch.liquibase.xmlutil.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree as ET

import pytest

from liquisketch.liquibase.exceptions import LiquibaseReadingError
from liquisketch.liquibase.xmlutil import (
    is_database_changelog,
    local_name,
    parse_database_changelog,
    resolve_include_path,
)


def test_local_name_strips_clark_namespace() -> None:
    """``local_name`` strips XML namespace from Clark notation."""
    assert local_name("{http://www.liquibase.org/xml/ns/dbchangelog}createTable") == "createTable"


def test_local_name_plain_tag_unchanged() -> None:
    """Tags without braces pass through unchanged."""
    assert local_name("createTable") == "createTable"


def test_is_database_changelog() -> None:
    """``is_database_changelog`` recognizes the root element name."""
    ns = "http://www.liquibase.org/xml/ns/dbchangelog"
    assert is_database_changelog(ET.Element(f"{{{ns}}}databaseChangeLog")) is True
    assert is_database_changelog(ET.Element("databaseChangeLog")) is True
    assert is_database_changelog(ET.Element(f"{{{ns}}}foo")) is False


def test_parse_database_changelog_reads_minimal_file(tmp_path: Path) -> None:
    """``parse_database_changelog`` returns a document root with expected tag."""
    path = tmp_path / "changelog.xml"
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog"/>\n',
        encoding="utf-8",
    )
    root = parse_database_changelog(path)
    assert local_name(root.tag) == "databaseChangeLog"


def test_resolve_include_path_relative_to_changelog_dir() -> None:
    """``relativeToChangelogFile=true`` resolves paths next to the including file."""
    with TemporaryDirectory() as td:
        base = Path(td)
        target = base / "child.xml"
        target.write_text("<root/>", encoding="utf-8")
        ns = "http://www.liquibase.org/xml/ns/dbchangelog"
        include_el = ET.Element(f"{{{ns}}}include")
        include_el.set("file", "child.xml")
        include_el.set("relativeToChangelogFile", "true")
        resolved = resolve_include_path(include_el, base)
        assert resolved == target.resolve()


@pytest.mark.parametrize("flag", ["true", "1", "yes"])
def test_resolve_include_relative_flag_variants(flag: str) -> None:
    """``relativeToChangelogFile`` accepts common truthy spellings."""
    with TemporaryDirectory() as td:
        base = Path(td)
        (base / "inc.xml").write_text("<root/>", encoding="utf-8")
        ns = "http://www.liquibase.org/xml/ns/dbchangelog"
        el = ET.Element(f"{{{ns}}}include", file="inc.xml", relativeToChangelogFile=flag)
        assert resolve_include_path(el, base).name == "inc.xml"


def test_resolve_include_missing_file_raises() -> None:
    """Missing ``file`` on ``<include>`` raises :exc:`LiquibaseReadingError`."""
    ns = "http://www.liquibase.org/xml/ns/dbchangelog"
    el = ET.Element(f"{{{ns}}}include")
    with pytest.raises(LiquibaseReadingError, match="missing file attribute"):
        resolve_include_path(el, Path("/tmp"))
