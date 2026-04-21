"""
Unit tests for liquisketch.liquibase.changeset_apply.
"""

from __future__ import annotations

from xml.etree import ElementTree as ET

import pytest

from liquisketch.liquibase.changeset_apply import apply_changeset_to_schema, changeset_ref_from_element
from liquisketch.liquibase.exceptions import LiquibaseReadingError
from liquisketch.schema import DatabaseSchema


_NS = "http://www.liquibase.org/xml/ns/dbchangelog"


def _change_set_element(inner_xml: str) -> ET.Element:
    """Parse ``inner_xml`` into a single Liquibase ``changeSet`` element."""
    doc = f"""<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog xmlns="{_NS}">
<changeSet id="unit" author="test">{inner_xml}</changeSet>
</databaseChangeLog>"""
    root = ET.fromstring(doc)
    return root[0]


def _apply_snippet(schema: DatabaseSchema, inner_xml: str) -> DatabaseSchema:
    """Apply one change set built from ``inner_xml`` to ``schema``."""
    return apply_changeset_to_schema(schema, changeset_ref_from_element(_change_set_element(inner_xml)))


def test_create_table_and_columns() -> None:
    """``createTable`` fills columns and constraint flags."""
    schema = DatabaseSchema(name="empty")
    _apply_snippet(
        schema,
        """
        <createTable tableName="users">
            <column name="id" type="BIGINT">
                <constraints primaryKey="true" nullable="false"/>
            </column>
            <column name="email" type="VARCHAR(255)">
                <constraints nullable="false" unique="true"/>
            </column>
        </createTable>
        """,
    )
    assert len(schema.tables) == 1
    users = schema.tables[0]
    assert users.name == "users"
    assert {c.name for c in users.columns} == {"id", "email"}
    id_col = next(c for c in users.columns if c.name == "id")
    assert id_col.primary_key is True
    assert id_col.nullable is False


def test_create_duplicate_table_raises() -> None:
    """Second ``createTable`` for the same name raises."""
    schema = DatabaseSchema(name="empty")
    inner = """
        <createTable tableName="dup"><column name="id" type="INT"><constraints nullable="false"/></column></createTable>
    """
    _apply_snippet(schema, inner)
    with pytest.raises(LiquibaseReadingError, match="already exists"):
        _apply_snippet(schema, inner)


def test_add_foreign_key_after_tables_exist() -> None:
    """``addForeignKeyConstraint`` attaches an outgoing FK on the base table."""
    schema = DatabaseSchema(name="empty")
    _apply_snippet(
        schema,
        """
        <createTable tableName="users">
            <column name="id" type="BIGINT"><constraints primaryKey="true" nullable="false"/></column>
        </createTable>
        <createTable tableName="posts">
            <column name="id" type="BIGINT"><constraints primaryKey="true" nullable="false"/></column>
            <column name="user_id" type="BIGINT"><constraints nullable="false"/></column>
        </createTable>
        """,
    )
    _apply_snippet(
        schema,
        """
        <addForeignKeyConstraint
            constraintName="fk_posts_user"
            baseTableName="posts"
            baseColumnNames="user_id"
            referencedTableName="users"
            referencedColumnNames="id"/>
        """,
    )
    posts = next(t for t in schema.tables if t.name == "posts")
    assert len(posts.foreign_keys) == 1
    fk = posts.foreign_keys[0]
    assert fk.name == "fk_posts_user"
    assert fk.source_table == "posts"
    assert fk.target_table == "users"


def test_drop_foreign_key_then_drop_table() -> None:
    """Drop FK then table leaves the referenced table intact."""
    schema = DatabaseSchema(name="empty")
    _apply_snippet(
        schema,
        """
        <createTable tableName="users">
            <column name="id" type="BIGINT"><constraints primaryKey="true" nullable="false"/></column>
        </createTable>
        <createTable tableName="refs">
            <column name="user_id" type="BIGINT"><constraints nullable="false"/></column>
        </createTable>
        <addForeignKeyConstraint
            constraintName="fk_refs_user"
            baseTableName="refs"
            baseColumnNames="user_id"
            referencedTableName="users"
            referencedColumnNames="id"/>
        """,
    )
    _apply_snippet(
        schema,
        """
        <dropForeignKeyConstraint baseTableName="refs" constraintName="fk_refs_user"/>
        <dropTable tableName="refs"/>
        """,
    )
    assert {t.name for t in schema.tables} == {"users"}
    for t in schema.tables:
        assert t.foreign_keys == []


def test_drop_foreign_key_missing_constraint_raises() -> None:
    """Dropping a non-existent FK name raises."""
    schema = DatabaseSchema(name="empty")
    _apply_snippet(
        schema,
        """
        <createTable tableName="t"><column name="a" type="INT"><constraints nullable="false"/></column></createTable>
        """,
    )
    with pytest.raises(LiquibaseReadingError, match="Foreign key not found"):
        _apply_snippet(schema, '<dropForeignKeyConstraint baseTableName="t" constraintName="nope"/>')


def test_add_column_and_modify_data_type() -> None:
    """``addColumn`` and ``modifyDataType`` update the column model."""
    schema = DatabaseSchema(name="empty")
    _apply_snippet(
        schema,
        """
        <createTable tableName="items">
            <column name="id" type="BIGINT"><constraints primaryKey="true" nullable="false"/></column>
        </createTable>
        """,
    )
    _apply_snippet(
        schema,
        """
        <addColumn tableName="items">
            <column name="label" type="VARCHAR(32)"><constraints nullable="true"/></column>
        </addColumn>
        """,
    )
    _apply_snippet(
        schema,
        """
        <modifyDataType tableName="items" columnName="label" newDataType="TEXT"/>
        """,
    )
    items = schema.tables[0]
    label = next(c for c in items.columns if c.name == "label")
    assert label.data_type == "TEXT"


def test_drop_column_removes_foreign_keys_referencing_column() -> None:
    """Dropping a column removes FKs that referenced it."""
    schema = DatabaseSchema(name="empty")
    _apply_snippet(
        schema,
        """
        <createTable tableName="users">
            <column name="id" type="BIGINT"><constraints primaryKey="true" nullable="false"/></column>
        </createTable>
        <createTable tableName="posts">
            <column name="user_id" type="BIGINT"><constraints nullable="false"/></column>
        </createTable>
        <addForeignKeyConstraint
            constraintName="fk_p_u"
            baseTableName="posts"
            baseColumnNames="user_id"
            referencedTableName="users"
            referencedColumnNames="id"/>
        """,
    )
    _apply_snippet(schema, '<dropColumn tableName="users" columnName="id"/>')
    posts = next(t for t in schema.tables if t.name == "posts")
    assert posts.foreign_keys == []


def test_rename_table_updates_foreign_key_table_names() -> None:
    """``renameTable`` rewrites FK source/target table names."""
    schema = DatabaseSchema(name="empty")
    _apply_snippet(
        schema,
        """
        <createTable tableName="users">
            <column name="id" type="BIGINT"><constraints primaryKey="true" nullable="false"/></column>
        </createTable>
        <createTable tableName="posts">
            <column name="user_id" type="BIGINT"><constraints nullable="false"/></column>
        </createTable>
        <addForeignKeyConstraint
            constraintName="fk"
            baseTableName="posts"
            baseColumnNames="user_id"
            referencedTableName="users"
            referencedColumnNames="id"/>
        """,
    )
    _apply_snippet(schema, '<renameTable oldTableName="users" newTableName="accounts"/>')
    fk = next(t for t in schema.tables if t.name == "posts").foreign_keys[0]
    assert fk.target_table == "accounts"


def test_rename_column_updates_foreign_key_columns() -> None:
    """``renameColumn`` updates FK column references."""
    schema = DatabaseSchema(name="empty")
    _apply_snippet(
        schema,
        """
        <createTable tableName="users">
            <column name="id" type="BIGINT"><constraints primaryKey="true" nullable="false"/></column>
        </createTable>
        <createTable tableName="posts">
            <column name="user_id" type="BIGINT"><constraints nullable="false"/></column>
        </createTable>
        <addForeignKeyConstraint
            constraintName="fk"
            baseTableName="posts"
            baseColumnNames="user_id"
            referencedTableName="users"
            referencedColumnNames="id"/>
        """,
    )
    _apply_snippet(
        schema,
        """
        <renameColumn tableName="users" oldColumnName="id" newColumnName="pk"/>
        """,
    )
    fk = next(t for t in schema.tables if t.name == "posts").foreign_keys[0]
    assert fk.target_column == "pk"


def test_unsupported_change_element_is_skipped() -> None:
    """Unknown change types are ignored without error."""
    schema = DatabaseSchema(name="empty")
    _apply_snippet(schema, "<weirdFutureLiquibaseTagDoesNotExist/>")
    assert not schema.tables


def test_operation_on_missing_table_raises() -> None:
    """Mutations against a missing table raise."""
    schema = DatabaseSchema(name="empty")
    with pytest.raises(LiquibaseReadingError, match="Table not found"):
        _apply_snippet(schema, '<addColumn tableName="ghost"><column name="x" type="INT"/></addColumn>')
