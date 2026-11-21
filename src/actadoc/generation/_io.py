"""Writing generated documents to disk (input/output kept out of the generation logic)."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from actadoc.generation._builder import GeneratedDocument


def write_corpus(documents: Iterable[GeneratedDocument], out_dir: Path) -> list[Path]:
    """Write each document as ``<doc_id>.txt`` and its ground truth as ``<doc_id>.json``.

    Parameters
    ----------
    documents : iterable of GeneratedDocument
        Documents to write.
    out_dir : pathlib.Path
        Destination directory, created if needed. Existing files with the
        same identifiers are overwritten, so that regenerating is idempotent.

    Returns
    -------
    list of pathlib.Path
        Paths of the written files, text then ground truth for each document.

    Raises
    ------
    NotADirectoryError
        If ``out_dir`` exists and is not a directory.
    """
    out_dir = Path(out_dir)
    if out_dir.exists() and not out_dir.is_dir():
        raise NotADirectoryError(f"{out_dir} exists and is not a directory")
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for doc in documents:
        stem = out_dir / doc.ground_truth.doc_id
        text_path = stem.with_suffix(".txt")
        truth_path = stem.with_suffix(".json")
        text_path.write_text(doc.text, encoding="utf-8", newline="\n")
        truth_path.write_text(
            doc.ground_truth.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n"
        )
        written += [text_path, truth_path]
    return written
