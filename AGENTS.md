# deploydiff

## Purpose
Compare deployment configurations across environments. Detect drift between staging and production configs. Preview infrastructure changes with human-readable diffs, cost impact estimation, and rollback commands.

## Build & Test Commands
- Install: `pip install -e .` or `pip install deploydiff`
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