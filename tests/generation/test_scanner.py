"""Turning a rendered PDF into a scanned, image-only PDF."""

import numpy as np
import pytest
from pypdf import PdfReader

from actadoc.generation import (
    DocumentType,
    ScanLevel,
    ScanRecord,
    count_pages,
    generate_documents,
    rasterize_pdf,
    render_pdf,
    scan_pdf,
)

DPI = 100  # low resolution keeps the tests fast


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    doc = generate_documents(DocumentType.LEASE, n=1, seed=42)[0]
    path = tmp_path_factory.mktemp("rendered") / "lease-00000.pdf"
    return render_pdf(doc, path)


def scanned_page(path):
    """Exact pixels of the first page, read from the image stored in the scanned PDF."""
    image = PdfReader(path).pages[0].images[0].image
    return np.asarray(image.convert("L"), dtype=int)


def scan(rendered, out, level="heavy", seed=1):
    return scan_pdf(rendered, out, doc_id="lease-00000", level=level, seed=seed, dpi=DPI)


def test_rasterized_pages_are_grayscale_a4(rendered):
    pages = rasterize_pdf(rendered, DPI)
    assert len(pages) == len(PdfReader(rendered).pages)
    height, width = pages[0].shape
    assert pages[0].dtype == np.uint8
    assert (width, height) == pytest.approx((8.27 * DPI, 11.69 * DPI), abs=2)  # A4 in inches


def test_invalid_resolution_is_rejected(rendered):
    with pytest.raises(ValueError, match="dpi"):
        rasterize_pdf(rendered, 0)


def test_scan_writes_an_image_only_pdf_and_its_record(rendered, tmp_path):
    out = tmp_path / "lease-00000.scan.pdf"
    record = scan(rendered, out)
    reader = PdfReader(out)
    assert len(reader.pages) == len(record.pages) == len(PdfReader(rendered).pages)
    assert "".join(page.extract_text() for page in reader.pages).strip() == ""  # no text layer
    saved = ScanRecord.model_validate_json((tmp_path / "lease-00000.scan.json").read_text())
    assert saved == record
    assert (saved.level, saved.seed, saved.dpi) == (ScanLevel.HEAVY, 1, DPI)


def test_same_inputs_give_identical_bytes(rendered, tmp_path):
    scan(rendered, tmp_path / "a" / "doc.scan.pdf")
    scan(rendered, tmp_path / "b" / "doc.scan.pdf")
    assert (tmp_path / "a" / "doc.scan.pdf").read_bytes() == (
        tmp_path / "b" / "doc.scan.pdf"
    ).read_bytes()


def test_different_seeds_give_different_scans(rendered, tmp_path):
    first = scan(rendered, tmp_path / "a.scan.pdf", seed=1)
    second = scan(rendered, tmp_path / "b.scan.pdf", seed=2)
    assert first.pages != second.pages


def test_heavy_scan_is_further_from_the_original_than_a_clean_one(rendered, tmp_path):
    original = rasterize_pdf(rendered, DPI)[0].astype(int)
    error = {}
    for level in ("clean", "heavy"):
        scan(rendered, tmp_path / f"{level}.scan.pdf", level=level)
        page = scanned_page(tmp_path / f"{level}.scan.pdf")
        error[level] = np.abs(page - original).mean()
    assert error["clean"] < 2  # only the scanner's JPEG compression
    assert error["heavy"] > 3 * error["clean"]


def test_unknown_level_is_rejected(rendered, tmp_path):
    with pytest.raises(ValueError):
        scan(rendered, tmp_path / "x.scan.pdf", level="extreme")


def test_count_pages(rendered):
    assert count_pages(rendered) == len(PdfReader(rendered).pages) >= 1
