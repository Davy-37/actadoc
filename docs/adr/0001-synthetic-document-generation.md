# ADR 0001 — Design of the synthetic document generator

- Status: Accepted
- Date: 2026-11-22
- Issue: #12 (sub-issue of #2)

## Context

ACTADOC needs a corpus of French real-estate documents whose entities are known exactly, for three document types, reproducible from a seed. Three risks drive the design:

1. **Wrong offsets.** If `start`/`end` are computed by hand from a template, one changed word shifts every following offset and silently corrupts the ground truth used by all evaluations.
2. **Growth.** Two more document types will follow, then PDF rendering and scan degradation. Adding them must not require editing existing generators.
3. **Reproducibility.** A corpus must be rebuilt identically, and a single document must be regenerable for debugging.

## Decision

1. **Builder for text and spans.** `DocumentBuilder` appends text and entities in reading order and computes offsets from the current length. Offsets are correct by construction, and `GeneratedDocument` re-checks `text[start:end] == value` on creation.
2. **Template Method for generators.** `DocumentGenerator.generate` fixes the shared steps (seed Faker and `random`, create the builder, build and validate); subclasses only implement `_compose`.
3. **Registry and factory.** Generators register with a class decorator; `get_generator(doc_type)` instantiates the right one. Adding a type means adding a class, with no `if/elif` to maintain.
4. **Per-document seed.** Each document's seed is derived from `(type, corpus seed, index)` and stored in its ground truth.
5. **Pure core, input/output at the edge.** Generation returns objects in memory; only `_io.write_corpus` touches the disk, and `scripts/generate_corpus.py` only parses arguments.
6. **Immutable, strict data model.** Pydantic models are frozen and reject unknown fields.

## Alternatives considered

| Option | Why not chosen |
|---|---|
| Text templates (Jinja2, `str.format`) then search each value in the rendered text to find offsets | A value can appear twice (deposit equal to rent) and the search would return the wrong occurrence; the builder avoids searching altogether |
| Hard-coded offsets in the template | Breaks as soon as a word changes; the risk 1 above |
| One `generate_document(doc_type)` function with `if/elif` per type | Simple for one type, but every new type edits the same function; tests and reviews get harder |
| A single corpus-level `random.Random(seed)` | Document `k` would depend on all previous draws: changing `n` or a template changes every following document |
| Dataclasses instead of Pydantic | No validation and no JSON round trip for free; Pydantic is already a project dependency |

## Consequences

Positive:
- Offset errors are impossible to introduce through the builder, and detected by validation otherwise.
- A new document type is one new module, one decorator, one import, and its tests.
- Any document can be regenerated alone from its stored seed.
- The generation logic is tested without the disk; the disk code is tested with temporary directories.

Negative and limits:
- Templates are written as chained Python calls, less readable for a non-developer than a plain text template.
- The registry relies on an import side effect: a generator module that is not imported is not registered (mitigated by importing every generator in `generation/__init__.py`, and by a test per type).
- Reproducibility holds only for a given Faker version (pinned to `>=40.0,<41.0`).
- Template Method couples subclasses to the base class: a type that needs a very different pipeline would require changing the base class or a new abstraction.
