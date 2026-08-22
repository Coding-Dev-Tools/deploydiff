# Changelog

All notable changes to DeployDiff CLI will be documented in this file.

## [Unreleased]

### Added

- CLI test suite with 14 tests for diff_renderer covering sensitive values, destructive warnings, empty plans, all providers, grouping, and edge cases (#11)
- `--exit-on-destroy` flag for CI/CD gating — exit non-zero if any destructive changes detected (#8)
- `--threshold` flag to fail CI when estimated cost exceeds a dollar amount (#8)
- MCP server integration via `mcp` subcommand with dedicated documentation
- GitHub Actions: GitHub Pages deployment workflow
- GitHub Actions: npm publish workflow (release or manual dispatch)
- GitHub Actions: OIDC trusted publisher for PyPI (removes PYPI_API_TOKEN dependency)
- `CONTRIBUTING.md` with development setup and PR guidelines
- `SECURITY.md` with security policy
- Homebrew and Scoop install methods
- Directory listing badges: Open Source Alternative, LibHunt, Awesome Python
- npm wrapper (`package.json` + `cli.js`) for npm publishing
- npm keywords optimized for discoverability (15 terms)
- `FUNDING.yml` for GitHub Sponsors
- GitHub issue templates, PR template, and Dependabot config
- `revenueholdings-license` gating on all CLI commands
- Beta badge and star CTA in README header

### Changed

- CI test matrix expanded to include Python 3.13
- CI security hardened: `persist-credentials: false`, restricted permissions
- Documentation branding updated from DevForge to Revenue Holdings
- README rewritten with CI/CD examples, alternatives comparison, MCP docs, and unified pricing
- README tool count updated (8 → 11)
- npm section removed from README (npm install instructions consolidated)
- PyPI publish switched to OIDC trusted publisher
- `project.urls` metadata added to `pyproject.toml`

### Fixed

- GitHub Actions versions downgraded to stable v4/v5 (v6 caused workflow parse failures)
- All three parsers (Terraform, CloudFormation, Pulumi) now raise a clear `FileNotFoundError` when input is neither valid JSON nor an existing file path, instead of a cryptic `FileNotFoundError`/`PermissionError` from `open()`
- Removed dead `.get()` calls in terraform_parser and cloudformation_parser (orphaned `data.get("planned_values")`, `data.get("output_changes")`, `resource_change_data.get("Scope")`, `data.get("StackName")`) that looked like they were processing data but silently discarded results — silent-failure traps removed
- YAML indentation in CI workflows
- Git merge conflicts resolved in dependabot.yml, publish.yml, and pyproject.toml
- UTF-8 encoding (mojibake) in file output
- Ruff lint issues: `datetime.UTC`, `X | None` syntax, `E501`, `B904`, `F821`, `F541` (f-string prefix)
- Missing `ruff` dev dependency in `pyproject.toml`
- Unused `pyyaml` dependency removed
- Broken Homebrew/Scoop code blocks in README install section
- `click_to_mcp` import wrapped in try/except for optional dependency
- `__pycache__` removed from git tracking; `.gitignore` corrected
- `.venv/` removed from git tracking; `.gitignore` corrected
- Broken PyPI badges replaced with GitHub release badge
- Dependencies bumped via Dependabot (checkout@v6, setup-node@v6, setup-python@v6)

## [0.1.0] — 2026-05-14

### Added

- Initial release
- Infrastructure change preview with resource summary (creates, updates, deletes, replaces)
- Property-level diffs with before/after values
- Cost impact estimation per resource
- Rollback command generation
- Terraform plan JSON support
- CloudFormation change set support
- Pulumi preview support
- Destructive action highlighting
- CI/CD integration with exit code gating
