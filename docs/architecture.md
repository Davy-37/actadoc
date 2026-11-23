# Architecture

Status: **in progress**. `actadoc.generation` is implemented for the 3 document types (leases, sale agreements, energy certificates), as text and PDF (see [generation.md](generation.md)); the other blocks are planned.

## Purpose

ACTADOC analyses heterogeneous French real-estate and legal PDFs (residential leases, sale agreements, energy performance certificates): it extracts structured information, classifies documents with calibrated confidence, detects anomalies, and answers questions over the corpus with systematic source citations.

## Processing chain

```
PDF → routing (native / scanned)
    → OpenCV preprocessing → OCR                  [ingestion]
    → 3-class classification + calibration        [classification]
    → NER (6 entity types) + abstention           [extraction]
    → chunking → embeddings → pgvector            [retrieval]
    → cross-encoder reranking → citations         [retrieval]
    → LLM orchestration + constrained output      [llm]
    → consistency rules, PDF forensics            [anomalies]
    → containerized FastAPI                       [api]
```

## Components

| Subpackage | Role | Main tools |
|---|---|---|
| `actadoc.generation` | Synthetic corpus with native labels, scan degradation | Faker (`fr_FR`), WeasyPrint, OpenCV |
| `actadoc.ingestion` | Native/scanned routing, preprocessing, OCR | pdfplumber, PyMuPDF, docTR, Tesseract |
| `actadoc.classification` | Lease / sale agreement / energy certificate, calibrated | scikit-learn, CamemBERT |
| `actadoc.extraction` | Parties, amounts, dates, cadastral references, surfaces, termination clauses | Transformers, spaCy |
| `actadoc.retrieval` | Chunking, embeddings, vector search, reranking | sentence-transformers, PostgreSQL 16 + pgvector (HNSW), bge-reranker |
| `actadoc.llm` | Multi-provider orchestration, Pydantic-validated outputs | Ollama, provider APIs |
| `actadoc.anomalies` | Cross-document consistency, perceptual hashing, PDF forensics | pypdf, imagehash, datasketch |
| `actadoc.api` | HTTP service | FastAPI |

Optional dependency groups in `pyproject.toml` match these blocks (`generation`, `ingestion`, `nlp`, `rag`, `llm`, `anomalies`, `api`), so each block installs only what it needs.

### Design choice: pgvector rather than a dedicated vector database

At this volume, one persistence system is enough: PostgreSQL 16 with the pgvector extension and an HNSW index avoids running and securing a second database.

## Architecture principles

These principles apply to every block. Significant decisions are recorded as [ADRs](adr/README.md).

| Principle | In practice |
|---|---|
| **Separation of concerns** | One module, one responsibility (schema, building, formatting, input/output) |
| **Pure core, input/output at the edge** | Business logic returns objects in memory; disk, network, databases and the command line stay in thin outer modules (`_io.py`, `scripts/`, `api/`) |
| **Dependencies point inward** | Outer layers (scripts, API) import the core; the core never imports them |
| **Open for extension, closed for modification** | New document types, OCR engines or LLM providers are added as new classes behind a common interface and a registry, not as new `if/elif` branches |
| **Program to an interface** | Callers depend on an abstract base class (`DocumentGenerator`), not on a concrete one |
| **Validate at the boundaries** | Data entering or leaving a block is a validated, immutable Pydantic model |
| **Public API in `__init__.py`** | Implementation in `_` modules; users import from the subpackage only |
| **Patterns only when they remove a real risk** | Each pattern used is justified in an ADR, with the simpler alternative it replaces |

## Repository layout

```
src/actadoc/       library (public API in each __init__.py, internals in _*.py)
evaluation/        evaluation sets: RAG questions, hallucination checks, altered documents
scripts/           entry points (corpus generation, evaluation runs)
docker/            container configuration
tests/             pytest suite, one sub-folder per block (tests/generation/, …)
docs/              technical documentation (this folder)
data/              never versioned: raw/, synthetic/, real/
```

## Data and confidentiality

- **Synthetic corpus**: generated from public templates (service-public.fr, Légifrance, ADEME open data, DVF) filled with Faker values, rendered to PDF and degraded to simulate scanning. The inserted value is the ground truth. Rebuilt with `scripts/generate_corpus.py` and a fixed seed.
- **Real corpus**: about 50 public or anonymized documents, annotated by hand. Stored only in `data/real/`, ignored by Git, **never published, logged or sent to an external service**.
- **LLM providers**: an API that sends data outside is not used on real documents (GDPR). The cost/latency/confidentiality trade-off is measured in [METRICS.md](../METRICS.md).
- **Model licenses**: checked before use; several document-understanding models (LayoutLM, Donut families) are non-commercial.

| Source | License | Usage |
|---|---|---|
| _to be completed before first use_ | | |
