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
