"""
Read/write and synchronize Draw.io diagrams against ``DatabaseSchema``.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import zlib
from pathlib import Path
from urllib.parse import quote, unquote
from xml.etree import ElementTree as ET

from liquisketch.schema import DatabaseSchema, Table

LOG = logging.getLogger(__name__)

TABLE_HEADER_HEIGHT = 28
COLUMN_ROW_HEIGHT = 24
TABLE_WIDTH = 360
TABLE_MARGIN_X = 40
TABLE_MARGIN_Y = 40
TABLE_GAP_X = 420
TABLE_GAP_Y = 80


def sync_schema_to_drawio(path: Path, schema: DatabaseSchema) -> None:
    """
    Synchronize a Draw.io diagram file with ``schema``.

    If ``path`` does not exist, a new uncompressed Draw.io file is created.
    """
    LOG.debug("Drawio sync started: output=%s schema=%s", path, schema.name)
    drawio = _DrawioFile.load(path)
    diagram_root = ET.fromstring(drawio.diagram_xml)
    _sync_graph_model(diagram_root, schema)
    drawio.diagram_xml = ET.tostring(diagram_root, encoding="unicode")
    drawio.save(path)
    LOG.debug("Drawio sync finished: output=%s", path)


class _DrawioFile:
    """
    In-memory representation of a Draw.io file and its compression mode.
    """

    def __init__(self, mxfile: ET.Element, diagram_xml: str, compressed: bool) -> None:
        self.mxfile = mxfile
        self.diagram_xml = diagram_xml
        self.compressed = compressed

    @classmethod
    def load(cls, path: Path) -> _DrawioFile:
        """Load a drawio file and decode the diagram content if needed."""
        if not path.exists():
            LOG.debug("Drawio file does not exist, creating new uncompressed document: %s", path)
            mxfile = ET.Element("mxfile", host="app.diagrams.net", version="24.0.0")
            ET.SubElement(mxfile, "diagram", id="liquisketch", name="Page-1")
            graph = _new_graph_model()
            return cls(mxfile=mxfile, diagram_xml=ET.tostring(graph, encoding="unicode"), compressed=False)

        tree = ET.parse(path)
        mxfile = tree.getroot()
        diagram = mxfile.find("diagram")
        if diagram is None:
            msg = "Invalid drawio file: missing <diagram> element"
            raise ValueError(msg)

        diagram_text = _extract_diagram_content(diagram)
        stripped = diagram_text.lstrip()
        if stripped.startswith("<"):
            LOG.debug("Loaded drawio in uncompressed XML mode: %s", path)
            return cls(mxfile=mxfile, diagram_xml=diagram_text, compressed=False)

        decoded = _decode_compressed_diagram(diagram_text)
        LOG.debug("Loaded drawio in compressed mode: %s", path)
        return cls(mxfile=mxfile, diagram_xml=decoded, compressed=True)

    def save(self, path: Path) -> None:
        """Persist the drawio file, preserving the original compression mode."""
        diagram = self.mxfile.find("diagram")
        if diagram is None:
            msg = "Invalid drawio file: missing <diagram> element"
            raise ValueError(msg)
        diagram_id = diagram.get("id", "liquisketch")
        diagram_name = diagram.get("name", "Page-1")

        if self.compressed:
            diagram.clear()
            diagram.text = _encode_compressed_diagram(self.diagram_xml)
            diagram.set("id", diagram_id)
            diagram.set("name", diagram_name)
            LOG.debug("Saved drawio in compressed mode: %s", path)
        else:
            graph_model = ET.fromstring(self.diagram_xml)
            diagram.clear()
            diagram.append(graph_model)
            diagram.set("id", diagram_id)
            diagram.set("name", diagram_name)
            LOG.debug("Saved drawio in uncompressed XML mode: %s", path)

        path.parent.mkdir(parents=True, exist_ok=True)
        ET.ElementTree(self.mxfile).write(path, encoding="utf-8", xml_declaration=True)


def _decode_compressed_diagram(content: str) -> str:
    raw = base64.b64decode(content)
    inflated = zlib.decompress(raw, wbits=-15)
    return unquote(inflated.decode("utf-8"))


def _encode_compressed_diagram(content: str) -> str:
    escaped = quote(content, safe="~()*!.'")
    compressor = zlib.compressobj(level=9, wbits=-15)
    compressed = compressor.compress(escaped.encode("utf-8"))
    compressed += compressor.flush()
    return base64.b64encode(compressed).decode("ascii")


def _new_graph_model() -> ET.Element:
    model = ET.Element(
        "mxGraphModel",
        dx="1200",
        dy="800",
        grid="1",
        gridSize="1",
        guides="1",
        tooltips="1",
        connect="1",
        arrows="1",
        fold="1",
        page="1",
        pageScale="1",
        pageWidth="2000",
        pageHeight="1400",
        math="0",
        shadow="0",
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")
    return model


def _sync_graph_model(graph_model: ET.Element, schema: DatabaseSchema) -> None:
    root = graph_model.find("root")
    if root is None:
        msg = "Invalid graph model: missing root"
        raise ValueError(msg)

    existing_state = _collect_managed_state(root)
    target_state = _collect_target_state(schema)
    _log_sync_events(existing_state, target_state)

    table_positions = _collect_table_positions(graph_model)
    managed = [cell for cell in root.findall("mxCell") if cell.get("lsKind")]
    for cell in managed:
        root.remove(cell)
    table_rows = _render_tables(root, schema.tables, table_positions)
    _render_foreign_keys(root, schema.tables, table_rows)


def _collect_table_positions(graph_model: ET.Element) -> dict[str, tuple[float, float]]:
    root = graph_model.find("root")
    if root is None:
        return {}
    positions: dict[str, tuple[float, float]] = {}
    for cell in root.findall("mxCell"):
        if cell.get("lsKind") != "table":
            continue
        table_name = cell.get("lsTable")
        geo = cell.find("mxGeometry")
        if not table_name or geo is None:
            continue
        x = float(geo.get("x", "0"))
        y = float(geo.get("y", "0"))
        positions[table_name] = (x, y)
    return positions


def _collect_managed_state(root: ET.Element) -> dict[str, set[str]]:
    """Collect current managed tables/columns/fks from diagram root."""
    tables: set[str] = set()
    columns: set[str] = set()
    foreign_keys: set[str] = set()

    for cell in root.findall("mxCell"):
        kind = cell.get("lsKind")
        if kind == "table":
            table_name = cell.get("lsTable")
            if table_name:
                tables.add(table_name)
        elif kind == "column":
            table_name = cell.get("lsTable")
            column_name = cell.get("lsColumn")
            if table_name and column_name:
                columns.add(f"{table_name}.{column_name}")
        elif kind == "fk":
            source = cell.get("source")
            target = cell.get("target")
            if source and target:
                foreign_keys.add(f"{source}->{target}")

    return {"tables": tables, "columns": columns, "fks": foreign_keys}


def _collect_target_state(schema: DatabaseSchema) -> dict[str, set[str]]:
    """Collect expected managed tables/columns/fks from schema."""
    tables: set[str] = set()
    columns: set[str] = set()
    foreign_keys: set[str] = set()

    for table in schema.tables:
        tables.add(table.name)
        for column in table.columns:
            columns.add(f"{table.name}.{column.name}")
        for fk in table.foreign_keys:
            source_row_id = _table_row_id(fk.source_table, fk.source_column)
            target_row_id = _table_row_id(fk.target_table, fk.target_column)
            foreign_keys.add(
                f"{source_row_id}->{target_row_id}"
            )

    return {"tables": tables, "columns": columns, "fks": foreign_keys}


def _log_sync_events(existing_state: dict[str, set[str]], target_state: dict[str, set[str]]) -> None:
    """Log add/delete/update counts for tables, columns, and foreign keys."""
    _log_kind_events("table", existing_state["tables"], target_state["tables"])
    _log_kind_events("column", existing_state["columns"], target_state["columns"])
    _log_kind_events("fk", existing_state["fks"], target_state["fks"])


def _log_kind_events(kind: str, existing_items: set[str], target_items: set[str]) -> None:
    """Log synchronization events for one managed item kind."""
    added = target_items - existing_items
    deleted = existing_items - target_items
    updated = existing_items & target_items
    for item in sorted(added):
        LOG.debug("Drawio sync %s add: %s", kind, item)
    for item in sorted(updated):
        LOG.debug("Drawio sync %s update: %s", kind, item)
    for item in sorted(deleted):
        LOG.debug("Drawio sync %s delete: %s", kind, item)


def _table_position(
    table_name: str,
    index: int,
    known_positions: dict[str, tuple[float, float]],
) -> tuple[float, float]:
    if table_name in known_positions:
        return known_positions[table_name]
    col = index % 4
    row = index // 4
    x = TABLE_MARGIN_X + (col * TABLE_GAP_X)
    y = TABLE_MARGIN_Y + (row * (TABLE_HEADER_HEIGHT + 7 * COLUMN_ROW_HEIGHT + TABLE_GAP_Y))
    return (float(x), float(y))


def _add_table_cells(
    root: ET.Element,
    table: Table,
    x: float,
    y: float,
    table_rows: dict[str, list[str]],
) -> None:
    table_id = _table_id(table.name)
    table_height = TABLE_HEADER_HEIGHT + max(len(table.columns), 1) * COLUMN_ROW_HEIGHT
    table_cell = ET.SubElement(
        root,
        "mxCell",
        id=table_id,
        value=table.name,
        style=(
            "shape=swimlane;startSize=28;horizontal=1;"
            "rounded=1;fontStyle=1;swimlaneFillColor=#f5f5f5;fillColor=#ffffff;"
            "strokeColor=#666666;collapsible=0;html=1;"
        ),
        vertex="1",
        parent="1",
        lsKind="table",
        lsTable=table.name,
    )
    ET.SubElement(
        table_cell,
        "mxGeometry",
        x=str(x),
        y=str(y),
        width=str(TABLE_WIDTH),
        height=str(table_height),
        **{"as": "geometry"},
    )

    row_ids = _add_column_rows(root, table, table_id)
    table_rows[table.name] = row_ids


def _extract_diagram_content(diagram: ET.Element) -> str:
    """Return diagram XML from text content or embedded child XML."""
    diagram_text = diagram.text or ""
    if diagram_text.strip():
        return diagram_text
    children = list(diagram)
    if not children:
        return ""
    return ET.tostring(children[0], encoding="unicode")


def _render_tables(
    root: ET.Element,
    tables: list[Table],
    table_positions: dict[str, tuple[float, float]],
) -> dict[str, list[str]]:
    """Render tables and columns and return a mapping of table to row ids."""
    table_rows: dict[str, list[str]] = {}
    ordered_tables = sorted(tables, key=lambda table: table.name.lower())
    for index, table in enumerate(ordered_tables):
        x, y = _table_position(table.name, index, table_positions)
        _add_table_cells(root, table, x, y, table_rows)
    return table_rows


def _render_foreign_keys(
    root: ET.Element,
    tables: list[Table],
    table_rows: dict[str, list[str]],
) -> None:
    """Render foreign key edges for available source/target column rows."""
    ordered_tables = sorted(tables, key=lambda table: table.name.lower())
    for table in ordered_tables:
        for fk in table.foreign_keys:
            source_row = table_rows.get(fk.source_table, [])
            target_row = table_rows.get(fk.target_table, [])
            source_row_id = _table_row_id(fk.source_table, fk.source_column)
            target_row_id = _table_row_id(fk.target_table, fk.target_column)
            if source_row_id in source_row and target_row_id in target_row:
                _add_fk_edge(root, fk.name, source_row_id, target_row_id)


def _add_column_rows(root: ET.Element, table: Table, table_id: str) -> list[str]:
    """Render one row per table column and return the generated row ids."""
    row_ids: list[str] = []
    for idx, column in enumerate(table.columns):
        row_id = _table_row_id(table.name, column.name)
        row_ids.append(row_id)
        row_cell = ET.SubElement(
            root,
            "mxCell",
            id=row_id,
            value=_column_row_value(table, column.name, column.data_type, column.nullable, column.primary_key),
            style=(
                "shape=partialRectangle;connectable=1;html=1;top=0;left=0;right=0;"
                "bottom=1;spacingLeft=8;align=left;fontSize=12;strokeColor=#d6d6d6;"
                "fillColor=none;"
            ),
            vertex="1",
            parent=table_id,
            lsKind="column",
            lsTable=table.name,
            lsColumn=column.name,
        )
        ET.SubElement(
            row_cell,
            "mxGeometry",
            y=str(TABLE_HEADER_HEIGHT + idx * COLUMN_ROW_HEIGHT),
            width=str(TABLE_WIDTH),
            height=str(COLUMN_ROW_HEIGHT),
            **{"as": "geometry"},
        )
    return row_ids


def _column_row_value(
    table: Table,
    column_name: str,
    data_type: str,
    nullable: bool,
    primary_key: bool,
) -> str:
    """Build the visible label for one table column row."""
    marker = "PK" if primary_key else "FK" if _is_fk_column(table, column_name) else ""
    nullable_value = "NULL" if nullable else "NOT NULL"
    return f"{marker:2}  {column_name} : {data_type} [{nullable_value}]".strip()


def _add_fk_edge(root: ET.Element, fk_name: str, source_id: str, target_id: str) -> None:
    edge = ET.SubElement(
        root,
        "mxCell",
        id=_fk_id(fk_name, source_id, target_id),
        value=fk_name,
        style=(
            "edgeStyle=entityRelationEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;"
            "html=1;endArrow=block;endFill=0;startArrow=ERmany;startFill=1;"
            "strokeWidth=1.2;strokeColor=#4a4a4a;"
        ),
        edge="1",
        parent="1",
        source=source_id,
        target=target_id,
        lsKind="fk",
    )
    ET.SubElement(edge, "mxGeometry", relative="1", **{"as": "geometry"})


def _is_fk_column(table: Table, column_name: str) -> bool:
    for fk in table.foreign_keys:
        if fk.source_column == column_name:
            return True
    return False


def _table_id(table_name: str) -> str:
    return f"ls_table_{_digest(table_name)}"


def _table_row_id(table_name: str, column_name: str) -> str:
    return f"ls_col_{_digest(f'{table_name}.{column_name}')}"


def _fk_id(fk_name: str, source_id: str, target_id: str) -> str:
    return f"ls_fk_{_digest(f'{fk_name}:{source_id}->{target_id}')}"


def _digest(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
