# Contributing

Thanks for helping improve LiquiSketch.

LiquiSketch's goal is simple: **Liquibase in, diagrams out**. Contributions should move the project toward reliable changelog parsing and useful schema visualization.

## How to Contribute

1. Fork the repository on GitHub.
2. Clone your fork and enter the project directory.
3. Add remotes so you can sync from both project and template history:
   - `origin` -> your fork
   - `upstream` -> `git@github.com:starforge-universe/liquisketch.git`
   - `template` -> `git@github.com:starforge-universe/python-library-template.git` (optional, for template updates)
4. Create a feature branch from `main`.
5. Make focused changes with tests and docs where relevant.
6. Run checks locally before pushing.
7. Open a pull request with a clear description and test notes.

## Local Setup

```bash
pip install -e ".[dev]"
```

## Quality Checks

Run the following before opening or updating a PR:

```bash
make test
make lint
make test-cov
```

If CI fails, push follow-up commits until checks pass.

## Pull Request Expectations

- Keep PRs scoped and easy to review
- Include or update tests for behavior changes
- Update `README.md` or other docs for user-facing changes
- Respond to review feedback promptly

## Keeping Your Branch Current

```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main
```

If you are also syncing template updates, fetch and merge from `template/main` intentionally and in separate PRs where possible.

## Code of Conduct

- Be respectful and constructive
- Assume positive intent
- Focus feedback on code and outcomes

## Questions

Open an issue or pull request discussion for clarification on design, scope, or implementation details.
