# CI/CD

## Local checks: pre-commit

Configured in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml), installed once with `pre-commit install` (or `make hooks`). On every commit it runs:

- file hygiene: trailing whitespace, end of file, YAML/TOML syntax, large files, merge conflicts, private keys;
- **Black** (formatting);
- **Ruff** (linting, imports, NumPy docstring rules), with safe automatic fixes.

Run on the whole repository with `pre-commit run --all-files`. `make check` runs exactly what CI runs.

## Continuous integration: `ci.yaml`

Triggered on pull requests to `main` and on pushes to `main`.

| Job | What it does |
|---|---|
| `issue-link` | Fails if the PR description has no closing keyword (`Closes #N`, `Fixes #N`, `Resolves #N`) |
| `quality` | Runs all pre-commit hooks |
| `tests` | installs Pango (needed by WeasyPrint), then mypy + pytest with branch coverage, matrix **Ubuntu / macOS × Python 3.11 / 3.12** (4 jobs) |

## Release: `release.yml`

Triggered when a GitHub Release is published.

1. Checks that the tag (`vX.Y.Z`) matches the package `__version__`.
2. Builds the wheel and sdist with `python -m build`.
3. Installs the wheel in a clean virtual environment and imports it.
4. Publishes to PyPI with **Trusted Publishing** (`id-token: write`, environment `pypi`). No PyPI token is stored in GitHub.

PyPI setup (once): add a trusted publisher (pending publisher for the first release) with the repository, the workflow file name `release.yml` and the environment name `pypi`.

## Repository settings (maintainers)

- Branch protection on `main`: pull request required, required status checks (`issue-link`, `quality`, the 4 `tests` jobs), conversations resolved, linear history, no direct push and no force push, rules applied to administrators too.
- Required approvals: **0 while the project has a single maintainer** (GitHub does not let authors approve their own pull request), who reviews every diff before merging. Raised to 1 when a second maintainer joins.
- Merge method: **squash merge** only; delete branches after merge.
- Labels: `bug`, `enhancement`, `documentation`, `good first issue`, `help wanted`.
- Milestones group issues by release (e.g. `v0.2.0`).
