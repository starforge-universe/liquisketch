"""
Apply a single Liquibase changeSet to a DatabaseSchema in memory.
"""

from __future__ import annotations

import logging

from liquisketch.schema import Column, DatabaseSchema, ForeignKey, Table

from .exceptions import LiquibaseReadingError
from .types import ChangeSetRef
from .xmlutil import local_name

LOG = logging.getLogger(__name__)


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes")


def _find_table(schema: DatabaseSchema, table_name: str) -> Table | None:
    for t in schema.tables:
        if t.name == table_name:
            return t
    return None


def _require_table(schema: DatabaseSchema, table_name: str) -> Table:
    t = _find_table(schema, table_name)
    if t is None:
        msg = f"Table not found: {table_name}"
        raise LiquibaseReadingError(msg)
    return t


def _column_from_liquibase_column_element(column_el) -> Column:
    name = column_el.get("name")
    if not name:
        msg = "<column> missing name"
        raise LiquibaseReadingError(msg)
    data_type = column_el.get("type") or column_el.get("typeName") or "UNKNOWN"
    primary_key = False
    nullable = True
    unique = False
    default: str | None = column_el.get("defaultValue")
    for child in column_el:
        if local_name(child.tag) != "constraints":
            continue
        primary_key = _parse_bool(child.get("primaryKey"), False)
        nullable = _parse_bool(child.get("nullable"), True)
        unique = _parse_bool(child.get("unique"), False)
        if child.get("defaultValue") is not None:
            default = child.get("defaultValue")
    return Column(
        name=name,
        data_type=data_type,
        nullable=nullable,
        primary_key=primary_key,
        unique=unique,
        default=default,
    )


def _first_csv(column_names: str) -> str:
    part = column_names.split(",")[0].strip()
    return part


def _apply_create_table(schema: DatabaseSchema, el) -> None:
    table_name = el.get("tableName")
    if not table_name:
        msg = "<createTable> missing tableName"
        raise LiquibaseReadingError(msg)
    if _find_table(schema, table_name) is not None:
        msg = f"Table already exists: {table_name}"
        raise LiquibaseReadingError(msg)
    columns: list[Column] = []
    for child in el:
        if local_name(child.tag) != "column":
            continue
        columns.append(_column_from_liquibase_column_element(child))
    schema.tables.append(Table(name=table_name, columns=columns, foreign_keys=[]))
    LOG.debug("Extracted change: createTable table=%s columns=%d", table_name, len(columns))


def _apply_add_foreign_key(schema: DatabaseSchema, el) -> None:
    name = el.get("constraintName") or ""
    base_table = el.get("baseTableName")
    base_cols = el.get("baseColumnNames")
    ref_table = el.get("referencedTableName")
    ref_cols = el.get("referencedColumnNames")
    if not all([base_table, base_cols, ref_table, ref_cols]):
        msg = "<addForeignKeyConstraint> missing required attributes"
        raise LiquibaseReadingError(msg)
    table = _require_table(schema, base_table)
    fk = ForeignKey(
        name=name,
        source_table=base_table,
        source_column=_first_csv(base_cols),
        target_table=ref_table,
        target_column=_first_csv(ref_cols),
    )
    table.foreign_keys.append(fk)
    LOG.debug(
        "Extracted change: addForeignKey name=%s source=%s.%s target=%s.%s",
        fk.name or "<unnamed>",
        fk.source_table,
        fk.source_column,
        fk.target_table,
        fk.target_column,
    )


def _apply_drop_foreign_key(schema: DatabaseSchema, el) -> None:
    base_table = el.get("baseTableName")
    constraint = el.get("constraintName")
    if not base_table or not constraint:
        msg = "<dropForeignKeyConstraint> missing baseTableName or constraintName"
        raise LiquibaseReadingError(msg)
    table = _require_table(schema, base_table)
    keep = [fk for fk in table.foreign_keys if fk.name != constraint]
    if len(keep) == len(table.foreign_keys):
        msg = f"Foreign key not found on {base_table}: {constraint}"
        raise LiquibaseReadingError(msg)
    table.foreign_keys = keep
    LOG.debug("Extracted change: dropForeignKey table=%s name=%s", base_table, constraint)


def _apply_drop_table(schema: DatabaseSchema, el) -> None:
    table_name = el.get("tableName")
    if not table_name:
        msg = "<dropTable> missing tableName"
        raise LiquibaseReadingError(msg)
    before = len(schema.tables)
    schema.tables = [t for t in schema.tables if t.name != table_name]
    if len(schema.tables) == before:
        msg = f"Table not found for drop: {table_name}"
        raise LiquibaseReadingError(msg)
    for t in schema.tables:
        t.foreign_keys = [
            fk
            for fk in t.foreign_keys
            if table_name not in (fk.target_table, fk.source_table)
        ]
    LOG.debug("Extracted change: dropTable table=%s", table_name)


def _apply_add_column(schema: DatabaseSchema, el) -> None:
    table_name = el.get("tableName")
    if not table_name:
        msg = "<addColumn> missing tableName"
        raise LiquibaseReadingError(msg)
    table = _require_table(schema, table_name)
    for child in el:
        if local_name(child.tag) != "column":
            continue
        col = _column_from_liquibase_column_element(child)
        existing = {c.name for c in table.columns}
        if col.name in existing:
            msg = f"Column already exists: {table_name}.{col.name}"
            raise LiquibaseReadingError(msg)
        table.columns.append(col)
        LOG.debug("Extracted change: addColumn column=%s.%s", table_name, col.name)


def _apply_drop_column(schema: DatabaseSchema, el) -> None:
    table_name = el.get("tableName")
    column_name = el.get("columnName")
    if not table_name or not column_name:
        msg = "<dropColumn> missing tableName or columnName"
        raise LiquibaseReadingError(msg)
    table = _require_table(schema, table_name)
    before = len(table.columns)
    table.columns = [c for c in table.columns if c.name != column_name]
    if len(table.columns) == before:
        msg = f"Column not found: {table_name}.{column_name}"
        raise LiquibaseReadingError(msg)
    for t in schema.tables:
        t.foreign_keys = [
            fk
            for fk in t.foreign_keys
            if not (
                (fk.source_table == table_name and fk.source_column == column_name)
                or (fk.target_table == table_name and fk.target_column == column_name)
            )
        ]
    LOG.debug("Extracted change: dropColumn column=%s.%s", table_name, column_name)


def _apply_rename_table(schema: DatabaseSchema, el) -> None:
    old = el.get("oldTableName")
    new = el.get("newTableName")
    if not old or not new:
        msg = "<renameTable> missing oldTableName or newTableName"
        raise LiquibaseReadingError(msg)
    t = _require_table(schema, old)
    t.name = new
    for tab in schema.tables:
        for fk in tab.foreign_keys:
            if fk.source_table == old:
                fk.source_table = new
            if fk.target_table == old:
                fk.target_table = new
    LOG.debug("Extracted change: renameTable from=%s to=%s", old, new)


def _apply_rename_column(schema: DatabaseSchema, el) -> None:
    table_name = el.get("tableName")
    old = el.get("oldColumnName")
    new = el.get("newColumnName")
    if not table_name or not old or not new:
        msg = "<renameColumn> missing tableName, oldColumnName, or newColumnName"
        raise LiquibaseReadingError(msg)
    table = _require_table(schema, table_name)
    for col in table.columns:
        if col.name == old:
            col.name = new
            break
    else:
        msg = f"Column not found for rename: {table_name}.{old}"
        raise LiquibaseReadingError(msg)
    for tab in schema.tables:
        for fk in tab.foreign_keys:
            if fk.source_table == table_name and fk.source_column == old:
                fk.source_column = new
            if fk.target_table == table_name and fk.target_column == old:
                fk.target_column = new
    LOG.debug("Extracted change: renameColumn table=%s from=%s to=%s", table_name, old, new)


def _apply_modify_data_type(schema: DatabaseSchema, el) -> None:
    table_name = el.get("tableName")
    column_name = el.get("columnName")
    new_type = el.get("newDataType")
    if not table_name or not column_name or not new_type:
        msg = "<modifyDataType> missing tableName, columnName, or newDataType"
        raise LiquibaseReadingError(msg)
    table = _require_table(schema, table_name)
    for col in table.columns:
        if col.name == column_name:
            old_type = col.data_type
            col.data_type = new_type
            LOG.debug(
                "Extracted change: modifyDataType column=%s.%s from=%s to=%s",
                table_name,
                column_name,
                old_type,
                new_type,
            )
            return
    msg = f"Column not found: {table_name}.{column_name}"
    raise LiquibaseReadingError(msg)


_SKIP_CHANGE_TAGS = frozenset(
    {
        "comment",
        "rollback",
        "preConditions",
        "validCheckSum",
        "createIndex",
        "dropIndex",
        "sql",
        "sqlFile",
        "empty",
    }
)


def apply_changeset_to_schema(schema: DatabaseSchema, changeset: ChangeSetRef) -> DatabaseSchema:
    """
    Apply all structural changes in one changeSet to the schema (mutates in place).
    """
    el = changeset.element
    applied_changes = 0
    for child in el:
        tag = local_name(child.tag)
        if tag in _SKIP_CHANGE_TAGS:
            LOG.debug(
                "Skipping non-structural change tag=%s in changeSet id=%s",
                tag,
                changeset.changeset_id or "<missing>",
            )
            continue
        if tag == "createTable":
            _apply_create_table(schema, child)
            applied_changes += 1
        elif tag == "addForeignKeyConstraint":
            _apply_add_foreign_key(schema, child)
            applied_changes += 1
        elif tag == "dropForeignKeyConstraint":
            _apply_drop_foreign_key(schema, child)
            applied_changes += 1
        elif tag == "dropTable":
            _apply_drop_table(schema, child)
            applied_changes += 1
        elif tag == "addColumn":
            _apply_add_column(schema, child)
            applied_changes += 1
        elif tag == "dropColumn":
            _apply_drop_column(schema, child)
            applied_changes += 1
        elif tag == "renameTable":
            _apply_rename_table(schema, child)
            applied_changes += 1
        elif tag == "renameColumn":
            _apply_rename_column(schema, child)
            applied_changes += 1
        elif tag == "modifyDataType":
            _apply_modify_data_type(schema, child)
            applied_changes += 1
        else:
            # Unknown change types are ignored until the model supports them.
            LOG.debug(
                "Unknown change tag skipped: tag=%s in changeSet id=%s",
                tag,
                changeset.changeset_id or "<missing>",
            )
            continue
    LOG.debug(
        "Applied changeSet id=%s author=%s structural_changes=%d",
        changeset.changeset_id or "<missing>",
        changeset.author or "<missing>",
        applied_changes,
    )
    return schema


def changeset_ref_from_element(changeset_el) -> ChangeSetRef:
    """Wrap a Liquibase ``changeSet`` element as a :class:`~liquisketch.liquibase.types.ChangeSetRef`."""
    cid = changeset_el.get("id") or ""
    author = changeset_el.get("author") or ""
    return ChangeSetRef(changeset_id=cid, author=author, element=changeset_el)
