# LiquiSketch

Liquibase in, diagrams out - sketch your schema straight from your changelog.

LiquiSketch is a Python utility that reads Liquibase changelogs and produces schema diagrams to help teams understand structure, relationships, and change history.

## Why LiquiSketch

- Keep schema docs aligned with migration history
- Reduce manual diagram maintenance
- Improve onboarding and design reviews
- Catch schema drift earlier

## Quick Start (development)

From a clone of this repository:

```bash
pip install -e ".[dev]"
make check
```

## Installation

### From PyPI

Install the published package (requires Python 3.11+):

```bash
pip install liquisketch
```

This installs the `liquisketch` package and the **`liquisketch`** console script (see [Command line](#command-line)).

### From the GitHub repository

Install the latest default branch without cloning:

```bash
pip install "git+https://github.com/starforge-universe/liquisketch.git"
```

Pin a tag or branch:

```bash
pip install "git+https://github.com/starforge-universe/liquisketch.git@v1.0.1"
pip install "git+https://github.com/starforge-universe/liquisketch.git@main"
```

### Editable install from a local clone

For development, install in editable mode from the repo root:

```bash
git clone https://github.com/starforge-universe/liquisketch.git
cd liquisketch
pip install -e ".[dev]"
```

## Usage

### Command line

After installation, run **`liquisketch`** with two positional arguments:

1. **`CHANGELOG`** — path to your Liquibase **master** changelog XML (for example `changelog-master.xml`).
2. **`OUTPUT`** — path where the Draw.io diagram should be written (for example `schema.drawio`).

```bash
liquisketch path/to/changelog-master.xml path/to/output.drawio
```

Verbose logging (Liquibase parsing and Draw.io sync details):

```bash
liquisketch -v path/to/changelog-master.xml path/to/output.drawio
```

You can also invoke the package as a module (same arguments):

```bash
python -m liquisketch path/to/changelog-master.xml path/to/output.drawio
```

Show help:

```bash
liquisketch --help
```

### Example with the repository test fixture

```bash
liquisketch tests/db/changelog-master.xml tests/db/schema.drawio
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
