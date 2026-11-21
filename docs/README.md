# Technical documentation

This folder documents how ACTADOC is built and operated. It is written for contributors and maintainers. For the project overview and frozen scope, start with the [project README](../README.md); for the contribution process, see [CONTRIBUTING.md](../CONTRIBUTING.md).

| Page | Content |
|---|---|
| [architecture.md](architecture.md) | Purpose, processing chain, components, repository layout, data and confidentiality |
| [generation.md](generation.md) | Synthetic corpus generation: usage, ground-truth format, design |
| [adr/](adr/README.md) | Architecture Decision Records: why each significant design choice was made |
| [ci-cd.md](ci-cd.md) | Pre-commit, CI and release workflows |

One page per block is added as it is implemented (ingestion, classification, extraction, retrieval, LLM, anomalies, API).

## Status convention

- **Implemented**: present in the code and covered by tests.
- **Planned**: designed and documented, not implemented yet.

When a pull request implements a planned item, it updates the status in the same pull request.

## Keeping the documentation in sync

- API reference content comes from the NumPy-style docstrings in the code; these pages describe structure and design.
- A pull request that changes behavior, the public API or the deployment updates the matching page.
- Measured numbers go to [METRICS.md](../METRICS.md), known limits to [LIMITATIONS.md](../LIMITATIONS.md).
