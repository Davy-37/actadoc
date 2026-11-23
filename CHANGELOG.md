# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- README: outdated week-by-week schedule replaced by the list of blocks and target metrics; progress now tracked in issues and milestones (#14).
- Tests: one sub-folder per block in `tests/`, mirroring the package (`tests/generation/`); pytest runs in `importlib` import mode (#16).
- Contributing guide: several small commits per pull request; branch protection documented as configured (0 required approvals while there is a single maintainer) (#20).

### Added

- Scan simulation: degradations (rotation, noise, blur, JPEG, lighting, stamp, fold) at levels `clean`, `light`, `medium`, `heavy`; image-only scanned PDFs with a replayable `ScanRecord`; `--scan` and `--dpi` options in `scripts/generate_corpus.py` (#26).
- PDF rendering of generated documents: `to_html` and `render_pdf` (WeasyPrint, A4), reproducible bytes with `SOURCE_DATE_EPOCH`; `--pdf` option in `scripts/generate_corpus.py` (#24).
- Synthetic energy performance certificates (`EnergyCertificateGenerator`) with ground truth: owner, diagnostician, living area, annual cost range, issue and expiry dates; `energy_class` implementing the 2021 DPE double threshold (#22).
- Synthetic sale agreements (`SaleAgreementGenerator`) with ground truth: parties, cadastral reference, Carrez area, price, deposit, loan contingency, deed deadline and signature date; `format_cadastral_reference` formatter (#18).
- Open source governance: MIT license, contributing guide, code of conduct, security policy, issue templates (bug, feature, documentation) and pull request template.
- Quality tooling: pre-commit (Black, Ruff with NumPy docstring rules), coverage configuration, Makefile.
- CI workflow: mandatory issue link on pull requests, pre-commit checks, tests on Ubuntu and macOS with Python 3.11 and 3.12.
- Release workflow: build, wheel smoke test and PyPI Trusted Publishing on GitHub Release.
- Technical documentation in `docs/`.
- First test checking that the package version is a valid semantic version, so that CI passes (#1).
- Synthetic residential lease generation with exact ground truth, reproducible from a seed (`actadoc.generation`, `scripts/generate_corpus.py`) (#12).
- Technical documentation of the generator and first Architecture Decision Record (#12).
