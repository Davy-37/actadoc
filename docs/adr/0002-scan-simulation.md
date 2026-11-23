# ADR 0002 — Design of the scan simulation

- Status: Accepted
- Date: 2026-11-23
- Issue: #26 (sub-issue of #2)

## Context

The ingestion block (#3) must handle scanned PDFs, and its OCR error must be measured per degradation level. The synthetic corpus therefore needs scanned versions of its documents, with four constraints:

1. **Measurable levels.** A result such as "CER 4 % on `medium`" only means something if `medium` is defined precisely and the same everywhere.
2. **Traceability.** For a bad OCR result, we must know exactly what was done to that page.
3. **Reproducibility.** The same document, level and seed must give the same scanned PDF.
4. **Licences.** The project is MIT; dependencies must allow that.

## Decision

1. **Pure image operations.** Each degradation (`rotate`, `add_noise`, `blur`, `jpeg_compress`, `uneven_lighting`, `stamp`, `fold`) is a function from a grayscale page to a new page, tested alone. Only noise needs randomness, passed explicitly.
2. **Draw, then apply.** `sample_operations(profile, shape, rng)` draws the parameters of a page from the level's profile; `apply_operations(page, operations)` applies them, without randomness. Drawing is the only random step.
3. **Typed, self-applying records.** Each operation is a Pydantic model (`Rotate`, `Stamp`, `Noise`…) in a discriminated union on `name`, with validated parameters and an `apply` method. A `ScanRecord` (level, seed, resolution, operations per page) is written next to each scanned PDF. Noise stores the seed of its own generator, so a record replays the same page exactly.
4. **Levels as frozen profiles.** `clean`, `light`, `medium`, `heavy` are `ScanProfile` dataclasses of parameter ranges, in one table (`PROFILES`).
5. **pypdfium2 to rasterize, Pillow to write.** Pages are rendered in grayscale by pypdfium2 (BSD/Apache, ships its own PDFium) and saved by Pillow as an image-only PDF, with fixed dates.

## Alternatives considered

| Option | Why not chosen |
|---|---|
| Augraphy (library of document degradations) | Realistic effects, but many parameters, a heavier dependency, and harder to record each applied parameter exactly; can be added later as another operation |
| Albumentations | Designed for training-time augmentation of photos; good transforms, but no stamps or folds, and records are not its purpose |
| One `degrade(page, level, rng)` function | Shorter, but the parameters actually used are lost: no record, no replay, harder tests |
| Untyped `{"name": ..., "params": {...}}` records with an `if/elif` dispatcher | First version written; mypy could not check parameters and every new operation edited the dispatcher. Replaced by the typed union |
| PyMuPDF to rasterize | Fast and complete, but AGPL: not compatible with publishing ACTADOC under MIT without care |
| pdf2image (Poppler) | Needs a system binary in CI and on every machine |

## Consequences

- A new degradation is one function, one operation model with `apply`, one line in the union and in `sample_operations`; existing operations do not change.
- OCR results can be broken down by level and, through the records, by operation (e.g. error rate on stamped pages).
- Every scanned page goes through JPEG at quality 95 inside the PDF, as with a real scanner: `clean` is not lossless.
- The degradations are simple models of reality (single grayscale channel, synthetic stamps, straight folds); see [LIMITATIONS.md](../../LIMITATIONS.md). Realism must be checked against the real corpus (#6).
