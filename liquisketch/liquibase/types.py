"""
Types used when traversing Liquibase XML changelogs.
"""

from __future__ import annotations

from dataclasses import dataclass
from xml.etree import ElementTree as ET


@dataclass(slots=True)
class ChangeSetRef:
    """
    One Liquibase changeSet: metadata plus the raw XML element for its changes.
    """

    changeset_id: str
    author: str
    element: ET.Element
