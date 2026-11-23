"""Rendering of generated documents to HTML and PDF."""

import pytest

from actadoc.generation._render import to_html


def body(page):
    return page.split("<body>\n", 1)[1].split("\n</body>", 1)[0].split("\n")


def test_first_line_is_the_title_and_capital_lines_are_headings():
    text = "CONTRAT DE LOCATION\nLogement nu\n\nI. DÉSIGNATION DES PARTIES\nEntre les soussignés :"
    assert body(to_html(text)) == [
        "<h1>CONTRAT DE LOCATION</h1>",
        "<p>Logement nu</p>",
        "<h2>I. DÉSIGNATION DES PARTIES</h2>",
        "<p>Entre les soussignés :</p>",
    ]


@pytest.mark.parametrize(
    ("line", "tag"),
    [
        ("PERFORMANCE ÉNERGÉTIQUE ET CLIMATIQUE", "h2"),
        ("VI. CLAUSE RÉSOLUTOIRE", "h2"),
        ("Classe énergétique : D", "p"),
        ("- Jean Dupont, ci-après dénommé(e) « le bailleur » ;", "p"),
        ("Surface : 45,5 m²", "p"),
        ("123 456", "p"),  # no letter: not a heading
        ("ÉTÉ", "h2"),  # accented capitals
        ("été", "p"),  # accented lower case
    ],
)
def test_line_kind(line, tag):
    assert body(to_html("TITRE\n" + line))[1].startswith(f"<{tag}>")


def test_special_characters_are_escaped():
    assert body(to_html("T\nPrix < 5 & loyer > 2"))[1] == "<p>Prix &lt; 5 &amp; loyer &gt; 2</p>"


def test_empty_lines_are_dropped():
    assert body(to_html("\n\nTITRE\n\n\nTexte\n")) == ["<h1>TITRE</h1>", "<p>Texte</p>"]


def test_empty_text_gives_an_empty_page():
    assert body(to_html("")) == [""]


def test_page_is_standalone_utf8_html():
    page = to_html("TITRE")
    assert page.startswith("<!DOCTYPE html>")
    assert '<meta charset="utf-8">' in page
    assert "size: A4" in page


@pytest.fixture(scope="module")
def one_of_each():
    from actadoc.generation import DocumentType, generate_documents

    return [generate_documents(doc_type, n=1, seed=42)[0] for doc_type in DocumentType]


def pdf_text(path):
    from pypdf import PdfReader

    return " ".join(" ".join(page.extract_text() for page in PdfReader(path).pages).split())


def test_every_entity_can_be_read_back_from_the_pdf(one_of_each, tmp_path):
    from actadoc.generation import render_pdf

    for doc in one_of_each:
        path = render_pdf(doc, tmp_path / f"{doc.ground_truth.doc_id}.pdf")
        assert path.read_bytes().startswith(b"%PDF-")
        text = pdf_text(path)
        for entity in doc.ground_truth.entities:
            assert " ".join(entity.value.split()) in text, entity.role


def test_same_document_gives_identical_bytes(one_of_each, tmp_path, monkeypatch):
    import time

    from actadoc.generation import render_pdf

    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
    first = render_pdf(one_of_each[0], tmp_path / "a.pdf").read_bytes()
    now = time.time()
    monkeypatch.setattr(time, "time", lambda: now + 86_400)  # render "one day later"
    second = render_pdf(one_of_each[0], tmp_path / "b.pdf").read_bytes()
    assert first == second


def test_parent_directories_are_created(one_of_each, tmp_path):
    from actadoc.generation import render_pdf

    path = render_pdf(one_of_each[0], tmp_path / "a" / "b" / "doc.pdf")
    assert path.is_file()


def test_rendering_to_a_directory_is_rejected(one_of_each, tmp_path):
    from actadoc.generation import render_pdf

    with pytest.raises(IsADirectoryError):
        render_pdf(one_of_each[0], tmp_path)


def test_missing_weasyprint_gives_a_clear_error(one_of_each, tmp_path, monkeypatch):
    import sys

    from actadoc.generation import render_pdf

    monkeypatch.setitem(sys.modules, "weasyprint", None)  # makes the import fail
    with pytest.raises(ImportError, match="actadoc\\[generation\\]"):
        render_pdf(one_of_each[0], tmp_path / "doc.pdf")
