# Synthetic corpus generation

Status: **implemented** for the 3 document types (leases, sale agreements, energy performance certificates): text, ground truth, PDF rendering and scan simulation.

## Purpose

Every ACTADOC block (OCR, classification, extraction, retrieval) is evaluated on a corpus whose labels are known exactly. The generator inserts values into document templates and records where each value is: **the inserted value is the ground truth**. Labels are perfect, free, and the corpus can be rebuilt identically from a seed.

## Usage

### Command line

```bash
pip install -e ".[generation]"
python scripts/generate_corpus.py --type lease --n 200 --seed 42 --pdf
python scripts/generate_corpus.py --type lease --n 200 --seed 42 --scan medium   # implies --pdf
```

`--pdf` needs WeasyPrint and the Pango system library (`apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0` on Debian/Ubuntu, `brew install pango` on macOS, then `export DYLD_FALLBACK_LIBRARY_PATH=$(brew --prefix)/lib` if WeasyPrint cannot find `libgobject`).

Output, in `data/synthetic/lease/` (ignored by Git):

```
lease-00000.txt     document text
lease-00000.json    ground truth
lease-00000.pdf     A4 rendering (with --pdf or --scan)
lease-00000.scan.pdf   scanned, image-only PDF (with --scan)
lease-00000.scan.json  scan record: level, seed, resolution, operations per page
lease-00001.txt
...
```

### Python

```python
from actadoc.generation import DocumentType, generate_documents, render_pdf, write_corpus

docs = generate_documents(DocumentType.LEASE, n=200, seed=42)
doc = docs[0]
doc.text                        # full text of the lease
doc.ground_truth.entities[0]    # Entity(label='party', role='landlord', value=..., start=..., end=...)
write_corpus(docs, "data/synthetic/lease")
render_pdf(doc, "data/synthetic/lease/lease-00000.pdf")
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

## Sale agreements

Model: *compromis de vente* for a flat in a co-ownership building. Entities, in reading order:

| Role | Type | Generation rule |
|---|---|---|
| `seller`, `buyer` | party | Faker `fr_FR` names, always different |
| `cadastral_reference` | cadastral_reference | section of 1 or 2 letters, parcel 1 to 9999; displayed `section AB n° 123`, normalized `AB0123` (section padded to 2 characters, parcel to 4 digits) |
| `living_area` | surface | Carrez area, 15.0 to 149.9 m² |
| `price` | amount | 80 000 to 900 000 €, rounded to 1 000 € |
| `deposit` | amount | 5 % to 10 % of the price (usual range) |
| `loan_contingency` | termination_clause | one of 2 wordings of the loan *condition suspensive* |
| `deed_deadline` | date | 60 to 120 days after signature |
| `signature_date` | date | between 1 January 2024 and mid-2026 |

Example (`seed=42`, first document): `section LG n° 4794` at offsets 343–361, normalized `LG4794`; price `508 000,00 €` at 530–542; deposit `30 480,00 €` (6 %).

**Labelling choice.** The loan contingency is a *condition suspensive*: if the loan is refused, the sale never takes effect. A *clause résolutoire* ends a contract that already exists. Both are labelled `termination_clause` because they answer the same business question (which clause makes the contract fall?) and a 7th entity type would change the schema and the extraction block. The distinction is listed in [LIMITATIONS.md](../LIMITATIONS.md).

## Energy performance certificates

Model: DPE (*diagnostic de performance énergétique*) of a dwelling, 2021 method. Entities, in reading order:

| Role | Type | Generation rule |
|---|---|---|
| `owner`, `diagnostician` | party | Faker `fr_FR` names, always different; the diagnostician's company is in the text, not labelled |
| `living_area` | surface | 15.0 to 149.9 m² |
| `annual_cost_min`, `annual_cost_max` | amount | ±20 % around consumption × area × 0.12 €/kWh, rounded to 10 € |
| `issue_date` | date | between 1 January 2024 and mid-2026 |
| `expiry_date` | date | 10 years after the issue date (29 February becomes 28 February) |

Primary energy (50 to 550 kWh/m²/year), emissions and the energy class are written in the text but **not labelled**: they are not one of the 6 entity types. The class is computed by `energy_class`, from the 2021 double threshold: the worse of the primary energy class and the emissions class.

| Class | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| Primary energy (kWh/m²/year) | < 70 | < 110 | < 180 | < 250 | < 330 | < 420 | ≥ 420 |
| Emissions (kg CO2/m²/year) | < 6 | < 11 | < 30 | < 50 | < 70 | < 100 | ≥ 100 |

The stated class always matches the stated values, so that the anomaly block (#10) can later alter one of them and check that the inconsistency is detected.

Example (`seed=42`, first document): 194 kWh/m²/year and 37 kg CO2/m²/year give class D; costs `720,00 €` (offsets 531–539) to `1 090,00 €` (543–553).

## PDF rendering

`to_html(text)` lays the text out as an HTML page: first line as the title, lines in capital letters as section headings, other lines as paragraphs, everything escaped. `render_pdf(document, path)` renders that page to an A4 PDF with WeasyPrint.

- **The ground truth stays the text.** Offsets refer to `doc.text`, not to positions in the PDF. Tests read every PDF back with pypdf and check that each entity value is found (whitespace normalized), for the 3 document types. The OCR block (#3) is evaluated by comparing its output with `doc.text`.
- **Why HTML then PDF**: the layout is CSS, easy to change without touching generators; WeasyPrint handles French typography, accents and page breaks. Alternatives: ReportLab (layout coded in Python, more control, more code), LaTeX (excellent output, heavy system dependency), LibreOffice from `.docx` (realistic, slow and hard to run in CI).
- WeasyPrint is imported only inside `render_pdf`: the rest of `actadoc.generation` works without it.

## Scan simulation

`scan_pdf(pdf_path, out_path, doc_id, level, seed, dpi=200)` turns a rendered PDF into what a scanner would produce: pages rasterized in grayscale (pypdfium2), degraded, and saved as an **image-only PDF** (no text layer), with a record next to it.

| Level | Rotation | Noise σ | Blur kernel | JPEG quality | Lighting | Stamp | Fold |
|---|---|---|---|---|---|---|---|
| `clean` | – | – | – | – | – | – | – |
| `light` | ±0.5° | 2–5 | – | 80–95 | ≤ 10 % | – | – |
| `medium` | ±1.5° | 5–10 | 1 or 3 | 55–80 | ≤ 25 % | 1 page in 2 | 1 page in 2 |
| `heavy` | ±3° | 10–18 | 3 or 5 | 30–55 | ≤ 40 % | every page | every page |

Operations are applied in the order a real scan goes through: geometry (rotation), marks on the paper (fold, stamp), optics (lighting, blur), then sensor noise and compression. Every page is also stored as JPEG at quality 95 inside the PDF, as a scanner does: `clean` means no simulated damage, not a lossless page. Measured on a lease at 100 dpi, the mean gap per pixel with the rendered page is 0.2 (clean), 13 (light), 31 (medium) and 35 (heavy) gray levels.

**The ground truth does not change.** It describes the text; the OCR block (#3) is evaluated by comparing its output with `doc.text`, per level.

### Scan record

Real record of `lease-00000` (corpus seed 42) at level `heavy`, 200 dpi, shortened to 4 of its 7 operations:

```json
{
  "doc_id": "lease-00000",
  "level": "heavy",
  "seed": 1882777570,
  "dpi": 200,
  "pages": [[
    {"name": "rotate", "angle": -0.894},
    {"name": "stamp", "centre": [723, 849], "radius": 181, "text": "COPIE", "intensity": 0.557},
    {"name": "noise", "sigma": 17.18, "seed": 243831923},
    {"name": "jpeg", "quality": 44}
  ]],
  "container_quality": 95,
  "schema_version": "1.0"
}
```

Each operation is a typed model chosen by its `name` (Pydantic discriminated union): its parameters are validated when the record is read back, and `apply_operations(page, record.pages[0])` replays the same page exactly. The noise operation stores the seed of its own generator for that purpose.

Design choices and alternatives: [ADR 0002](adr/0002-scan-simulation.md).

## Corpus statistics

```bash
python scripts/corpus_stats.py --n 200 --seed 42
```

Generates the corpus, renders it to PDF in a temporary folder to count pages, and prints Markdown tables: documents (words, pages, entities), entities per type, DPE classes, and the share of scanned pages that get each degradation per level. The measured figures are in [METRICS.md](../METRICS.md); rerun the script whenever a generator changes.

The degradation rates are drawn exactly as `scan_pdf` draws them (one generator per document, one draw per page), without rasterizing: which operations a page gets does not depend on its size.

## Design

| Module | Role |
|---|---|
| `_schema.py` | Ground-truth data model (Pydantic, immutable) |
| `_builder.py` | `DocumentBuilder`: assembles text and computes offsets (Builder pattern) |
| `_base.py` | `DocumentGenerator` skeleton (Template Method), registry and factory, seeding, `generate_documents` |
| `_formats.py` | French formatting of amounts, dates, surfaces and cadastral references, shared by all document types |
| `_lease.py` | `LeaseGenerator`, the lease template |
| `_sale_agreement.py` | `SaleAgreementGenerator`, the sale agreement template |
| `_energy_classes.py` | `energy_class`: DPE class from the 2021 double threshold, pure function reusable by the anomaly block |
| `_energy_certificate.py` | `EnergyCertificateGenerator`, the DPE template |
| `_render.py` | `to_html` (pure) and `render_pdf` (writes the PDF) |
| `_degradation.py` | Image operations (rotate, noise, blur, JPEG, lighting, stamp, fold): pure functions on `uint8` pages |
| `_scan.py` | Levels and profiles, typed operation records, `sample_operations` and `apply_operations` |
| `_scanner.py` | `rasterize_pdf`, `count_pages` and `scan_pdf`: reads and writes PDFs |
| `_io.py` | `write_corpus`: writes text and ground truth |
| `_stats.py` | Corpus statistics: entities, words, DPE classes, degradation rates |

Decisions and trade-offs: [ADR 0001](adr/0001-synthetic-document-generation.md) (generators), [ADR 0002](adr/0002-scan-simulation.md) (scan simulation).

### Adding a document type

1. Add the type to `DocumentType`, then create `_<type>.py` with a class deriving from `DocumentGenerator`, decorated with `@register_generator(DocumentType.<TYPE>)`.
2. Implement `_compose(builder, fake, rng)` using `builder.text(...)` and `builder.entity(...)` in reading order.
3. Import the module in `actadoc/generation/__init__.py` so that it registers itself.
4. Add tests in `tests/generation/test_<type>.py`: reproducibility, expected roles, business rules.

No existing code changes: the registry finds the new generator. Checked with the sale agreement (#18) and the energy certificate (#22): `_base.py`, `_builder.py`, `_schema.py` and the existing generators were not modified.

## Reproducibility

- Each document gets its own seed, derived from `(document type, corpus seed, index)`. Document `k` is identical whatever `n` is, and can be regenerated alone.
- Dates are drawn from a fixed range, not from today's date.
- **PDF bytes**: embedded font subsets carry a timestamp. With `SOURCE_DATE_EPOCH` set (the script sets it to `0`), the same document gives identical bytes on the same machine. Fonts come from the system, so PDFs differ between machines (layout, glyphs); the text and the ground truth do not.
- **Scanned PDFs**: the same rendered PDF, level, seed and resolution give identical bytes (dates in the PDF are fixed). The script uses the document seed for the degradations, so one corpus seed regenerates text, PDFs and scans.
- **Limit**: Faker's output can change between versions. Faker is pinned to `>=40.0,<41.0`; the same seed is only guaranteed to give the same corpus with the same Faker version.
