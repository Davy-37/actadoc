"""Turn a rendered PDF into a scanned, image-only PDF (input/output at the edge)."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from actadoc.generation._degradation import Image
from actadoc.generation._scan import (
    PROFILES,
    ScanLevel,
    ScanRecord,
    apply_operations,
    sample_operations,
)


def rasterize_pdf(path: Path, dpi: int) -> list[Image]:
    """Render every page of a PDF to a grayscale image.

    Parameters
    ----------
    path : pathlib.Path
        PDF to read.
    dpi : int
        Resolution in dots per inch, ``>= 1``.

    Returns
    -------
    list of numpy.ndarray
        One grayscale ``uint8`` page per PDF page.

    Raises
    ------
    ValueError
        If ``dpi`` is not positive.
    """
    import pypdfium2 as pdfium

    if dpi < 1:
        raise ValueError(f"dpi must be positive, got {dpi}")
    document = pdfium.PdfDocument(Path(path))
    try:
        return [
            np.asarray(page.render(scale=dpi / 72, grayscale=True).to_pil(), dtype=np.uint8)
            for page in document
        ]
    finally:
        document.close()


def count_pages(path: Path) -> int:
    """Return the number of pages of a PDF.

    Parameters
    ----------
    path : pathlib.Path
        PDF to read.

    Returns
    -------
    int
        Number of pages.
    """
    import pypdfium2 as pdfium

    document = pdfium.PdfDocument(Path(path))
    try:
        return len(document)
    finally:
        document.close()


def scan_pdf(
    pdf_path: Path,
    out_path: Path,
    doc_id: str,
    level: ScanLevel,
    seed: int,
    dpi: int = 200,
) -> ScanRecord:
    """Simulate the scan of a rendered PDF.

    Pages are rasterized, degraded according to ``level`` and saved as an
    image-only PDF (no text layer, as from a real scanner). The record is
    written next to it, with the ``.json`` suffix.

    Parameters
    ----------
    pdf_path : pathlib.Path
        Rendered PDF, from :func:`render_pdf`.
    out_path : pathlib.Path
        Scanned PDF to write, e.g. ``lease-00000.scan.pdf``; the record goes
        to ``lease-00000.scan.json``.
    doc_id : str
        Identifier of the document, stored in the record and the PDF title.
    level : ScanLevel
        Degradation level.
    seed : int
        Seed of the degradations, ``>= 0``.
    dpi : int, default=200
        Scan resolution.

    Returns
    -------
    ScanRecord
        Level, seed, resolution and the operations applied to each page.

    Notes
    -----
    The same PDF, level, seed and resolution give identical bytes: the dates
    stored in the PDF are fixed to the Unix epoch.
    """
    from PIL import Image as PILImage

    level = ScanLevel(level)
    rng = np.random.default_rng(seed)
    pages = rasterize_pdf(pdf_path, dpi)
    operations = [sample_operations(PROFILES[level], page.shape, rng) for page in pages]
    record = ScanRecord(doc_id=doc_id, level=level, seed=seed, dpi=dpi, pages=operations)
    scanned = [
        PILImage.fromarray(apply_operations(page, ops))
        for page, ops in zip(pages, operations, strict=True)
    ]

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    epoch = time.gmtime(0)
    scanned[0].save(
        out_path,
        format="PDF",
        save_all=True,
        append_images=scanned[1:],
        resolution=dpi,
        quality=record.container_quality,
        title=doc_id,
        creationDate=epoch,
        modDate=epoch,
    )
    out_path.with_suffix(".json").write_text(
        record.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return record
