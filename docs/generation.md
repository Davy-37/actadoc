# Synthetic corpus generation

Status: **implemented** for residential leases (text and ground truth). **Planned**: sale agreements, energy performance certificates, PDF rendering, scan degradation (sub-issues of #2).

## Purpose

Every ACTADOC block (OCR, classification, extraction, retrieval) is evaluated on a corpus whose labels are known exactly. The generator inserts values into document templates and records where each value is: **the inserted value is the ground truth**. Labels are perfect, free, and the corpus can be rebuilt identically from a seed.

## Usage

### Command line

```bash
pip install -e ".[generation]"
python scripts/generate_corpus.py --type lease --n 200 --seed 42
```

Output, in `data/synthetic/lease/` (ignored by Git):

```
lease-00000.txt     document text
lease-00000.json    ground truth
lease-00001.txt
...
```

### Python

```python
from actadoc.generation import DocumentType, generate_documents, write_corpus

docs = generate_documents(DocumentType.LEASE, n=200, seed=42)
doc = docs[0]
doc.text                        # full text of the lease
doc.ground_truth.entities[0]    # Entity(label='party', role='landlord', value=..., start=..., end=...)
write_corpus(docs, "data/synthetic/lease")
```

## Ground-truth format (schema version 1.0)

Example: first lease of `generate_documents(DocumentType.LEASE, n=1, seed=42)` (two of its nine entities shown).

```json
{
  "doc_id": "lease-00000",
  "doc_type": "lease",
  "seed": 1882777570,
  "entities": [
    {"label": "party", "role": "landlord", "value": "Hélène Fischer",
     "normalized": null, "start": 193, "end": 207},
    {"label": "amount", "role": "rent", "value": "1 376,00 €",
     "normalized": "1376.00", "start": 655, "end": 665}
  ],
  "schema_version": "1.0"
}
```

| Field | Meaning |
|---|---|
| `label` | One of the 6 entity types: `party`, `amount`, `date`, `cadastral_reference`, `surface`, `termination_clause` |
| `role` | Precise role in the document (`landlord`, `rent`, `start_date`…) |
| `value` | Exact text, so that `text[start:end] == value` |
| `normalized` | Canonical form for evaluation: ISO 8601 date, decimal amount, decimal surface; `null` for parties and clauses |
| `start`, `end` | Character offsets in the text (end excluded) |
| `seed` | Seed of this document: `LeaseGenerator().generate(doc_id, seed)` regenerates it alone |

Invariants enforced by validation: offsets match the value length, entities are sorted and do not overlap, every entity matches the text.

## Residential leases

Model: standard unfurnished lease (law n° 89-462 of 6 July 1989). Entities, in reading order:

| Role | Type | Generation rule |
|---|---|---|
| `landlord`, `tenant` | party | Faker `fr_FR` names, always different |
| `living_area` | surface | 18.0 to 139.9 m² |
| `start_date` | date | 1 to 44 days after signature |
| `rent` | amount | 450 to 2 499 € per month |
| `service_charges` | amount | 30 to 249 € per month |
| `security_deposit` | amount | equal to one month of rent excluding charges (legal maximum for an unfurnished lease) |
| `termination` | termination_clause | one of 2 wordings (six-week notice after a payment order) |
| `signature_date` | date | between 1 January 2024 and mid-2026 |

## Design

| Module | Role |
|---|---|
| `_schema.py` | Ground-truth data model (Pydantic, immutable) |
| `_builder.py` | `DocumentBuilder`: assembles text and computes offsets (Builder pattern) |
| `_base.py` | `DocumentGenerator` skeleton (Template Method), registry and factory, seeding, `generate_documents` |
| `_formats.py` | French formatting of amounts, dates and surfaces, shared by all document types |
| `_lease.py` | `LeaseGenerator`, the lease template |
| `_io.py` | `write_corpus`: the only module that touches the disk |

Decisions and trade-offs: [ADR 0001](adr/0001-synthetic-document-generation.md).

### Adding a document type

1. Create `_sale_agreement.py` with a class deriving from `DocumentGenerator`, decorated with `@register_generator(DocumentType.SALE_AGREEMENT)`.
2. Implement `_compose(builder, fake, rng)` using `builder.text(...)` and `builder.entity(...)` in reading order.
3. Import the module in `actadoc/generation/__init__.py` so that it registers itself.
4. Add tests: reproducibility, expected roles, business rules.

No existing code changes: the registry finds the new generator.

## Reproducibility

- Each document gets its own seed, derived from `(document type, corpus seed, index)`. Document `k` is identical whatever `n` is, and can be regenerated alone.
- Dates are drawn from a fixed range, not from today's date.
- **Limit**: Faker's output can change between versions. Faker is pinned to `>=40.0,<41.0`; the same seed is only guaranteed to give the same corpus with the same Faker version.
