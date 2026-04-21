#!/usr/bin/env python3
"""
CLI entry point for LiquiSketch.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from liquisketch.drawio import sync_schema_to_drawio
from liquisketch.liquibase import LiquibaseReadingError, load_database_schema_from_master_changelog


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser for ``liquisketch``."""
    parser = argparse.ArgumentParser(
        prog="liquisketch",
        description="Turn Liquibase changelogs into DrawIO schema diagrams.",
    )
    parser.add_argument(
        "changelog",
        type=Path,
        metavar="CHANGELOG",
        help="Path to the Liquibase master changelog (e.g. changelog-master.xml).",
    )
    parser.add_argument(
        "output",
        type=Path,
        metavar="OUTPUT",
        help="Path for the generated DrawIO diagram (.drawio).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Run the LiquiSketch CLI and return a process exit code.
    """
    args = build_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )
    log = logging.getLogger("liquisketch")

    changelog: Path = args.changelog.expanduser().resolve()
    output: Path = args.output.expanduser()

    if not changelog.is_file():
        log.error("Changelog not found: %s", changelog)
        return 1

    log.debug("Input changelog: %s", changelog)
    log.debug("Output DrawIO: %s", output)
    try:
        schema = load_database_schema_from_master_changelog(changelog)
        sync_schema_to_drawio(output, schema)
    except (LiquibaseReadingError, OSError, ValueError) as exc:
        log.error("Failed to generate diagram: %s", exc)
        return 1

    log.info("Diagram generated: %s", output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
