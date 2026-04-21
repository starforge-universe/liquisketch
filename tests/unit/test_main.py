"""
Unit tests for liquisketch CLI entry point.
"""

from __future__ import annotations

from pathlib import Path

from liquisketch.__main__ import main


def test_main_generates_diagram_from_master_changelog(tmp_path: Path) -> None:
    """CLI loads schema from changelog and writes drawio output."""
    changelog = Path("tests/db/changelog-master.xml").resolve()
    output = tmp_path / "generated.drawio"
    exit_code = main([str(changelog), str(output)])
    assert exit_code == 0
    assert output.is_file()


def test_main_returns_error_for_missing_changelog(tmp_path: Path) -> None:
    """CLI returns non-zero when input changelog does not exist."""
    missing = tmp_path / "missing.xml"
    output = tmp_path / "generated.drawio"
    exit_code = main([str(missing), str(output)])
    assert exit_code == 1
