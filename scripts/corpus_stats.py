"""Measure the synthetic corpus and print the tables reported in ``METRICS.md``.

Usage::

    python scripts/corpus_stats.py --n 200 --seed 42

Documents are generated and rendered to PDF in a temporary folder (to count
pages); nothing is written to ``data/``.
"""

from __future__ import annotations

import argparse
import os
import tempfile
from datetime import date
from importlib.metadata import version
from pathlib import Path

from actadoc.generation import (
    OPERATION_NAMES,
    DocumentType,
    EntityType,
    GeneratedDocument,
    ScanLevel,
    Summary,
    count_pages,
    energy_class_counts,
    entity_counts,
    generate_documents,
    operation_rates,
    render_pdf,
    summarize,
    word_counts,
)


def _range(summary: Summary) -> str:
    """Format a summary as ``min / mean / max``."""
    return f"{summary.minimum:g} / {summary.mean:.1f} / {summary.maximum:g}"


def _table(header: list[str], rows: list[list[str]]) -> str:
    """Format a Markdown table."""
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def report(
    corpus: dict[DocumentType, list[GeneratedDocument]],
    pages: dict[DocumentType, list[int]],
    seed: int,
) -> str:
    """Format the statistics of a corpus as Markdown.

    Parameters
    ----------
    corpus : dict
        Documents of each type.
    pages : dict
        Number of PDF pages of each document, in the same order.
    seed : int
        Corpus seed, recorded in the report.

    Returns
    -------
    str
        Markdown tables: documents, entities, energy classes, degradations.
    """
    n = len(next(iter(corpus.values())))
    everything = [doc for docs in corpus.values() for doc in docs]
    parts = [
        f"Measured on {date.today().isoformat()}: {n} documents per type, corpus seed {seed}, "
        f"Faker {version('faker')}. Command: `python scripts/corpus_stats.py --n {n} --seed {seed}`."
    ]

    parts.append(
        _table(
            [
                "Type",
                "Documents",
                "Words (min / mean / max)",
                "PDF pages (min / mean / max)",
                "Entities",
            ],
            [
                [
                    f"`{t.value}`",
                    str(len(docs)),
                    _range(word_counts(docs)),
                    _range(summarize(pages[t])),
                    str(sum(len(d.ground_truth.entities) for d in docs)),
                ]
                for t, docs in corpus.items()
            ],
        )
    )

    per_type = {t: entity_counts(docs) for t, docs in corpus.items()}
    total = entity_counts(everything)
    parts.append(
        _table(
            ["Entity type", *(f"`{t.value}`" for t in corpus), "Total"],
            [
                [f"`{label.value}`", *(str(per_type[t][label]) for t in corpus), str(total[label])]
                for label in EntityType
            ],
        )
    )

    certificates = corpus.get(DocumentType.ENERGY_CERTIFICATE, [])
    if certificates:
        classes = energy_class_counts(certificates)
        parts.append(
            _table(
                ["DPE class", *classes],
                [
                    ["Certificates", *(str(c) for c in classes.values())],
                    ["Share", *(f"{c / len(certificates):.0%}" for c in classes.values())],
                ],
            )
        )

    pages_per_seed = [
        (doc.ground_truth.seed, n_pages)
        for t, docs in corpus.items()
        for doc, n_pages in zip(docs, pages[t], strict=True)
    ]
    levels = [level for level in ScanLevel if level is not ScanLevel.CLEAN]
    rates = {level: operation_rates(pages_per_seed, level) for level in levels}
    parts.append(
        "Share of scanned pages that get each operation (`clean`: none):\n\n"
        + _table(
            ["Operation", *(f"`{level.value}`" for level in levels)],
            [
                [f"`{name}`", *(f"{rates[lv][name]:.0%}" for lv in levels)]
                for name in OPERATION_NAMES
            ],
        )
    )
    return "\n\n".join(parts) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Generate the corpus, render it to count pages, and print the report.

    Parameters
    ----------
    argv : list of str or None, default=None
        Command-line arguments; ``None`` reads ``sys.argv``.

    Returns
    -------
    int
        Process exit code, ``0`` on success.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--n", type=int, default=200, help="documents per type")
    parser.add_argument("--seed", type=int, default=42, help="corpus seed")
    args = parser.parse_args(argv)

    os.environ.setdefault("SOURCE_DATE_EPOCH", "0")
    corpus = {t: generate_documents(t, n=args.n, seed=args.seed) for t in DocumentType}
    pages: dict[DocumentType, list[int]] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for t, docs in corpus.items():
            pages[t] = [
                count_pages(render_pdf(doc, Path(tmp) / f"{doc.ground_truth.doc_id}.pdf"))
                for doc in docs
            ]
    print(report(corpus, pages, args.seed), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
