"""Command-line entry point: generate the synthetic corpus into ``data/synthetic/``.

Usage::

    python scripts/generate_corpus.py --type lease --n 200 --seed 42 --pdf

The logic lives in :mod:`actadoc.generation`; this script only parses
arguments and reports what was written.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from actadoc.generation import DocumentType, generate_documents, render_pdf, write_corpus


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, generate the documents and write them.

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
    parser.add_argument("--type", default="lease", choices=[t.value for t in DocumentType])
    parser.add_argument("--n", type=int, default=200, help="number of documents")
    parser.add_argument("--seed", type=int, default=42, help="corpus seed")
    parser.add_argument("--out", type=Path, default=Path("data/synthetic"))
    parser.add_argument("--pdf", action="store_true", help="also render each document to PDF")
    args = parser.parse_args(argv)

    out_dir = args.out / args.type
    documents = generate_documents(DocumentType(args.type), n=args.n, seed=args.seed)
    paths = write_corpus(documents, out_dir)
    if args.pdf:
        # fixed font timestamps, so that the same corpus gives the same PDF bytes
        os.environ.setdefault("SOURCE_DATE_EPOCH", "0")
        paths += [render_pdf(doc, out_dir / f"{doc.ground_truth.doc_id}.pdf") for doc in documents]
    print(f"{len(documents)} {args.type} documents written to {out_dir} ({len(paths)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
