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
make test
make lint
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
