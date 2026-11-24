# Contributing to ACTADOC

Thanks for your interest in this project. Contributions of all sizes are welcome: bug reports, documentation fixes, tests, and code.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Scope

ACTADOC analyses French real-estate and legal documents (residential leases, sale agreements, energy performance certificates): OCR, classification with calibrated confidence, entity extraction with abstention, anomaly detection, and question answering over the corpus with systematic source citations. Its value is in **measured, honest results** on a synthetic corpus with native labels and a small real annotated set. The scope is frozen: see the README. See the [technical documentation](docs/).

## The workflow in one line

**Issue → branch → commits → pull request (`Closes #N`) → CI → review → squash merge.**

No change reaches `main` without an issue and a reviewed pull request. `main` is protected: direct pushes are blocked.

## 1. Start from an issue

Every change starts with an issue, even a small one. Use the [issue templates](.github/ISSUE_TEMPLATE):

- **Bug report**: a descriptive title, steps to reproduce, expected behavior, actual behavior.
- **Feature request**: description, motivation, expected behavior, examples.
- **Documentation**: location and what is missing or wrong.

Comment on the issue to say you are working on it, so a maintainer can assign it to you. Issues marked `good first issue` are a good place to start.

For security issues, **do not open a public issue**: follow [SECURITY.md](SECURITY.md).

## 2. Set up your fork

External contributors work from a fork:

```bash
# 1. Fork the repository on GitHub, then clone your fork
git clone <your-fork-url>
cd actadoc

# 2. Add the original project as upstream
git remote add upstream <original-repo-url>

# 3. Install the project and the pre-commit hooks
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

`origin` is your fork (you push there). `upstream` is the original project (you fetch from there).

No document is part of the repository. The synthetic corpus is rebuilt with `scripts/generate_corpus.py` (fixed seed). The real annotated documents are never published.

## 3. Create a branch

Keep your `main` in sync, then branch from it:

```bash
git fetch upstream
git switch main
git merge upstream/main
git push origin main
git switch -c feature/<short-name>
```

Branch names are short, lowercase, hyphenated, and say what the branch contains:

| Prefix | Use | Example |
|---|---|---|
| `feature/` | new functionality | `feature/scene-split` |
| `fix/` | bug fix | `fix/empty-manifest` |
| `docs/` | documentation only | `docs/api-reference` |
| `refactor/` | restructuring with no change in behavior (code or tests) | `refactor/tests-per-block` |
| `experiment/` | exploratory work, not meant to be merged as is | `experiment/onnx-export` |

## 4. Write the change

### Code standards

- Python 3.11+.
- **Formatting**: [Black](https://black.readthedocs.io/). **Linting**: [Ruff](https://docs.astral.sh/ruff/). **Types**: mypy. All three are configured in `pyproject.toml` and run by pre-commit and CI.
- **Package layout**: implementation lives in internal modules prefixed with `_` (e.g. `actadoc/<subpackage>/_module.py`). The public API is exposed by each subpackage's `__init__.py`. Users import `from actadoc.<subpackage> import <name>`, never from a `_` module.
- Do not commit data, model weights, or secrets. Configuration goes through environment variables (`.env`, never committed).

### Design and architecture

- Follow the [architecture principles](docs/architecture.md#architecture-principles): separation of concerns, pure core with input/output at the edge, extension through new classes and registries rather than `if/elif`, validated immutable data at boundaries.
- Use a design pattern only when it removes a concrete risk or duplication, and say which one in the pull request.
- Record any significant design decision as an [Architecture Decision Record](docs/adr/README.md): context, alternatives considered, decision, consequences.

### Docstrings (required)

Every public module, class, function and method has a [NumPy-style docstring](https://numpydoc.readthedocs.io/en/latest/format.html). Ruff enforces it (`D` rules, `numpy` convention).

```python
def word_count(text: str) -> int:
    """Count the number of words in a string.

    Parameters
    ----------
    text : str
        Input text whose words are counted.

    Returns
    -------
    int
        Number of words in the input text.

    Raises
    ------
    TypeError
        If ``text`` is not a string.
    """
```

- Class docstrings document the constructor parameters (`Parameters`) and public attributes (`Attributes`); `__init__` is not documented separately.
- Private helpers (`_name`) need a short one-line docstring at least.

### Technical documentation

If your change modifies behavior, the public API, the pipeline or the deployment, update the matching page in [`docs/`](docs/) in the same pull request.

### Tests

- Tests use `pytest`, in files named `test_*.py`.
- `tests/` mirrors the package: **one sub-folder per block**, named like the sub-package it tests. Package-level tests stay at the root of `tests/`.

  ```
  tests/
    test_package.py        package metadata
    generation/            tests of src/actadoc/generation/
      test_schema.py
      test_lease.py
    extraction/            tests of src/actadoc/extraction/
  ```

- Inside a block folder, files are named after the module they test, without the block prefix (`generation/test_schema.py`, not `test_generation_schema.py`). Pytest runs in `importlib` mode, so two blocks can each have a `test_schema.py`.
- Cover **normal cases**, **edge cases** (empty input, boundaries, invalid values) and **expected exceptions** (`pytest.raises`).
- Use `@pytest.mark.parametrize` instead of copying the same test.
- **Every bug fix comes with a regression test** that fails before the fix and passes after.
- Check coverage with `make test`: the report lists the lines no test runs. Add tests for the ones that matter, with assertions on the result.

### Project rules

- **Real documents are never committed, published, logged or sent to an external service.** Only public or anonymized documents are used, and they stay in `data/real/`, which Git ignores.
- No personal data in code, tests, fixtures, issues or pull requests: use synthetic values generated with Faker (`fr_FR`).
- The synthetic corpus is reproducible from a seed; the inserted value is the ground truth.
- The gap between synthetic and real performance is measured and published in `METRICS.md`.
- Calibration and abstention thresholds are chosen on validation data, never on the test set.
- LLM providers are compared on cost, latency, schema compliance and confidentiality; a provider that sends data outside is not used on real documents (GDPR).
- Model licenses are checked before use (several document-understanding models are non-commercial).
- A value in `METRICS.md` is added only when measured, with date and protocol.

## 5. Commit

Use [Conventional Commits](https://www.conventionalcommits.org/), in English, in the imperative mood:

```
<type>(<optional scope>): <short summary, 72 characters max>

<optional body: why the change was needed>
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`, `ci`, `chore`.
Scopes: the subpackage or area changed (e.g. `api`, `ci`, `docs`).

Good: `feat(api): add health endpoint`, `fix(ci): cache pip dependencies`.
Bad: `update`, `fix`, `changes`, `final version`.

One commit is one logical change. Stage only the related files (`git add <files>`), not everything.

Prefer **several small commits** to one large commit. Each commit does one thing, can be read on its own, and passes pre-commit and the tests. For example, adding a document generator:

1. `feat(generation): add format_cadastral_reference` (formatter and its tests)
2. `feat(generation): add SaleAgreementGenerator` (generator and its tests)
3. `feat(generation): export SaleAgreementGenerator`
4. `docs(generation): document sale agreements`
5. `docs(changelog): add sale agreements`

Small commits make the review easier, and let you revert one step or find a regression with `git bisect` on the branch. Pull requests are squash-merged, so `main` still gets one commit per pull request.

pre-commit runs Black and Ruff on every commit. If a hook modifies a file, review the change, `git add` it again and commit again.

## 6. Open a pull request

```bash
git push -u origin feature/<short-name>
```

Then open a pull request from your branch to `main` and fill in the [template](.github/PULL_REQUEST_TEMPLATE.md):

- a clear title (Conventional Commits format, it becomes the squash commit message);
- **`Closes #N`** referencing the issue. **CI rejects a pull request without a linked issue**;
- what changed, why, and notes for reviewers.

### CI

On every pull request, GitHub Actions runs:

1. the issue-link check;
2. pre-commit (Black, Ruff, file checks);
3. mypy and the test suite with coverage on **Ubuntu and macOS**, with **Python 3.11 and 3.12**.

All checks must pass before merging. If a job fails, open it, read the failed step's log, reproduce locally (`make check`), fix, and push again: the pull request updates automatically.

### Review

A maintainer reviews every pull request before merging. Reviewers comment, approve, or request changes. Answer every comment, push new commits to the same branch, and do not open a new pull request for the same change.

### Merge

Maintainers merge with **Squash and Merge**: one pull request becomes one commit on `main`. The branch is then deleted (`git push origin --delete <branch>`).

## Releases (maintainers)

The project follows [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`):

- **PATCH**: backward-compatible bug fix;
- **MINOR**: new backward-compatible functionality;
- **MAJOR**: breaking change of the public API.

Release steps:

1. Update `__version__` in `src/actadoc/__init__.py` (single source of the version).
2. Move the `[Unreleased]` section of `CHANGELOG.md` under the new version and date.
3. Merge these changes through a pull request.
4. Tag the release commit and push the tag: `git tag -a v0.2.0 -m "v0.2.0"` then `git push origin v0.2.0`.
5. Create a GitHub Release from the tag, with the changelog section as release notes.
6. The [release workflow](.github/workflows/release.yml) checks that the tag matches the version, builds the wheel and sdist, tests the wheel, and publishes to PyPI through Trusted Publishing.

A public function is never removed directly: it is first deprecated (it keeps working, emits a `DeprecationWarning`, and the docstring names the replacement), then removed in the next major version.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
