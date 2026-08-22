# deploydiff

## Purpose
Compare deployment configurations across environments. Detect drift between staging and production configs. Preview infrastructure changes with human-readable diffs, cost impact estimation, and rollback commands.

## Build & Test Commands
- Install (editable, from this repo): `pip install -e .`
- Install (prebuilt wheel from the self-hosted index): `pip install --index-url https://coding-dev-tools.github.io/pypi-index/simple/ deploydiff`
- Install (from source): `pip install git+https://github.com/Coding-Dev-Tools/deploydiff.git`
- NOTE: `deploydiff` is NOT on public PyPI — use the self-hosted index or a `git+` URL above.
- Test: `pytest tests/` (or `python -m pytest tests/ -v --tb=short`)
- Lint: `ruff check .`
- Build: `pip install build twine && python -m build && twine check dist/*`
- CLI check: `deploydiff --help`

## Architecture
Key directories:
- `src/deploydiff/` — Main package (CLI, diff engine, cost estimator, rollback generator)
- `tests/` — Test suite
- `.github/workflows/` — CI/CD (auto-code-review.yml, ci.yml, pages.yml, publish.yml)
- `dist/` — Built distributions
- `scripts/` — Automation scripts

## Conventions
- Language: Python 3.10+
- Test framework: pytest
- CI: GitHub Actions (auto-code-review.yml, ci.yml, pages.yml, publish.yml)
- Linting: ruff
- Build system: setuptools
- Package layout: src/ layout
- Dependencies: click, rich, pyyaml, tomli, jinja2
- CLI entry point: deploydiff.cli:cli
- Default branch: main
- Versioning: Semantic versioning (semver)
- Documentation: Markdown

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines and development workflow.