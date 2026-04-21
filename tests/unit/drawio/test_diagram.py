"""
Unit tests for Draw.io schema synchronization.
"""

from __future__ import annotations

import base64
import zlib
from pathlib import Path
from urllib.parse import quote, unquote
from xml.etree import ElementTree as ET

from liquisketch.drawio import sync_schema_to_drawio
from liquisketch.schema import Column, DatabaseSchema, ForeignKey, Table


def test_sync_schema_creates_new_uncompressed_drawio_file(tmp_path: Path) -> None:
    """A missing output file is created as uncompressed XML draw.io content."""
    output = tmp_path / "schema.drawio"
    schema = DatabaseSchema(
        name="db",
        tables=[
            Table(
                name="orders",
                columns=[
                    Column(name="id", data_type="BIGINT", nullable=False, primary_key=True),
                    Column(name="customer_id", data_type="BIGINT", nullable=False),
                ],
                foreign_keys=[
                    ForeignKey(
                        name="fk_orders_customer",
                        source_table="orders",
                        source_column="customer_id",
                        target_table="customers",
                        target_column="id",
                    )
                ],
            ),
            Table(
                name="customers",
                columns=[Column(name="id", data_type="BIGINT", nullable=False, primary_key=True)],
            ),
        ],
    )

    sync_schema_to_drawio(output, schema)

    root = ET.parse(output).getroot()
    diagram = root.find("diagram")
    assert diagram is not None
    model = _diagram_model(diagram)
    serialized = ET.tostring(model, encoding="unicode")
    assert "orders" in serialized
    assert "customers" in serialized
    cells = model.findall("./root/mxCell")
    assert any(cell.get("lsKind") == "table" and cell.get("lsTable") == "orders" for cell in cells)
    assert any(cell.get("lsKind") == "column" and cell.get("lsColumn") == "customer_id" for cell in cells)
    assert any(cell.get("lsKind") == "fk" for cell in cells)


def test_sync_schema_keeps_compressed_mode(tmp_path: Path) -> None:
    """Compressed ``<diagram>`` content stays compressed after synchronization."""
    output = tmp_path / "schema-compressed.drawio"
    base_graph = '<mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/></root></mxGraphModel>'
    compressed = _encode_diagram_content(base_graph)
    output.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<mxfile><diagram id="p1" name="Page-1">{compressed}</diagram></mxfile>',
        encoding="utf-8",
    )

    schema = DatabaseSchema(
        name="db",
        tables=[
            Table(
                name="accounts",
                columns=[Column(name="id", data_type="UUID", nullable=False, primary_key=True)],
            )
        ],
    )

    sync_schema_to_drawio(output, schema)

    root = ET.parse(output).getroot()
    diagram = root.find("diagram")
    assert diagram is not None
    encoded = diagram.text or ""
    assert not encoded.lstrip().startswith("<")
    decoded = _decode_diagram_content(encoded)
    assert "<mxGraphModel" in decoded
    assert "accounts" in decoded


def test_sync_schema_removes_tables_not_in_schema(tmp_path: Path) -> None:
    """Tables absent from schema are removed during synchronization."""
    output = tmp_path / "schema-sync.drawio"
    output.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<mxfile><diagram id=\"p1\" name=\"Page-1\">"
        "<mxGraphModel><root>"
        "<mxCell id=\"0\"/>"
        "<mxCell id=\"1\" parent=\"0\"/>"
        "<mxCell id=\"ls_table_deadbeef\" lsKind=\"table\" lsTable=\"obsolete\" vertex=\"1\" parent=\"1\">"
        "<mxGeometry x=\"20\" y=\"20\" width=\"300\" height=\"120\" as=\"geometry\"/>"
        "</mxCell>"
        "</root></mxGraphModel>"
        "</diagram></mxfile>",
        encoding="utf-8",
    )

    schema = DatabaseSchema(
        name="db",
        tables=[
            Table(
                name="active_table",
                columns=[Column(name="id", data_type="INT", nullable=False, primary_key=True)],
            )
        ],
    )

    sync_schema_to_drawio(output, schema)

    root = ET.parse(output).getroot()
    diagram = root.find("diagram")
    assert diagram is not None
    model = _diagram_model(diagram)
    cells = model.findall("./root/mxCell")
    table_names = {cell.get("lsTable") for cell in cells if cell.get("lsKind") == "table"}
    assert table_names == {"active_table"}


def _encode_diagram_content(content: str) -> str:
    escaped = quote(content, safe="~()*!.'")
    compressor = zlib.compressobj(level=9, wbits=-15)
    compressed = compressor.compress(escaped.encode("utf-8")) + compressor.flush()
    return base64.b64encode(compressed).decode("ascii")


def _decode_diagram_content(content: str) -> str:
    raw = base64.b64decode(content)
    inflated = zlib.decompress(raw, wbits=-15).decode("utf-8")
    return unquote(inflated)


def _diagram_model(diagram: ET.Element) -> ET.Element:
    if list(diagram):
        return list(diagram)[0]
    return ET.fromstring(diagram.text or "")
