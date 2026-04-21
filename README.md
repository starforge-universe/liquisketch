# LiquiSketch

Liquibase in, diagrams out - sketch your schema straight from your changelog.

LiquiSketch is a Python utility that reads Liquibase changelogs and produces schema diagrams to help teams understand structure, relationships, and change history.

## Why LiquiSketch

- Keep schema docs aligned with migration history
- Reduce manual diagram maintenance
- Improve onboarding and design reviews
- Catch schema drift earlier

## Quick Start

```bash
pip install -e ".[dev]"
make check
```

## Usage

### Generate a diagram from a Liquibase master changelog

```bash
liquisketch tests/db/changelog-master.xml tests/db/schema.drawio
```

You can also run the module directly:

```bash
python -m liquisketch tests/db/changelog-master.xml tests/db/schema.drawio
```

### Synchronization behavior

- Creates the output file when it does not exist.
- Synchronizes tables, columns, and foreign keys with the changelog-derived schema.
- Removes diagram elements that no longer exist in schema.
- Keeps the original diagram format when updating an existing file:
  - compressed stays compressed
  - uncompressed stays uncompressed
- New files are written as uncompressed Draw.io XML.

### Python API

```python
from pathlib import Path

from liquisketch.drawio import sync_schema_to_drawio
from liquisketch.liquibase import load_database_schema_from_master_changelog

schema = load_database_schema_from_master_changelog(Path("tests/db/changelog-master.xml"))
sync_schema_to_drawio(Path("tests/db/schema.drawio"), schema)
```

## Project Layout

```text
liquisketch/
├── liquisketch/        # Package source
├── tests/              # Test suite
├── pyproject.toml      # Packaging and tooling configuration
├── Makefile            # Development commands
├── CONTRIBUTING.md     # Contributor workflow
└── README.md           # Project overview
```

## Contributing

See `CONTRIBUTING.md` for setup, workflow, and PR expectations.

## License

This project is licensed under `LICENSE`.
