"""
Dataclasses representing the core schema entities used by LiquiSketch.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Column:
    """
    A single database table column.
    """

    name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False
    unique: bool = False
    default: str | None = None


@dataclass(slots=True)
class ForeignKey:
    """
    A foreign key relation from one table column to another.
    """

    name: str
    source_table: str
    source_column: str
    target_table: str
    target_column: str


@dataclass(slots=True)
class Table:
    """
    A database table, including columns and outgoing foreign keys.
    """

    name: str
    columns: list[Column] = field(default_factory=list)
    foreign_keys: list[ForeignKey] = field(default_factory=list)


@dataclass(slots=True)
class DatabaseSchema:
    """
    Root schema object containing all tables in a database model.
    """

    name: str
    tables: list[Table] = field(default_factory=list)
