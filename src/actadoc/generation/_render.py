"""Rendering of generated documents to HTML and PDF."""

from __future__ import annotations

import html
from pathlib import Path

from actadoc.generation._builder import GeneratedDocument

# A4 page with the margins and fonts of an office document.
_STYLE = """
@page { size: A4; margin: 2.2cm 2cm; }
body { font-family: serif; font-size: 11pt; line-height: 1.35; }
h1 { font-size: 15pt; text-align: center; margin: 0 0 0.2em; }
h2 { font-size: 11.5pt; margin: 1.1em 0 0.3em; }
p { margin: 0 0 0.35em; text-align: justify; }
"""


def _is_heading(line: str) -> bool:
    """Tell whether a line is a section title, written in capital letters."""
    return any(c.isalpha() for c in line) and line == line.upper()


def to_html(text: str) -> str:
    r"""Turn the text of a generated document into a standalone HTML page.

    The first non-empty line becomes the title, lines in capital letters
    become section headings, other lines become paragraphs. Empty lines are
    dropped. Text is escaped, so every line is shown exactly as written.

    Parameters
    ----------
    text : str
        Full text of the document.

    Returns
    -------
    str
        HTML page with an embedded A4 stylesheet.

    Examples
    --------
    >>> page = to_html("BAIL\nLoyer : 850,00 € <net>")
    >>> "<h1>BAIL</h1>" in page, "<p>Loyer : 850,00 € &lt;net&gt;</p>" in page
    (True, True)
    """
    blocks: list[str] = []
    for line in text.split("\n"):
        if not line.strip():
            continue
        escaped = html.escape(line, quote=False)
        if not blocks:
            blocks.append(f"<h1>{escaped}</h1>")
        elif _is_heading(line):
            blocks.append(f"<h2>{escaped}</h2>")
        else:
            blocks.append(f"<p>{escaped}</p>")
    body = "\n".join(blocks)
    return (
        '<!DOCTYPE html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
        f"<style>{_STYLE}</style>\n</head>\n<body>\n{body}\n</body>\n</html>\n"
    )


def render_pdf(document: GeneratedDocument, path: Path) -> Path:
    """Render a generated document to an A4 PDF.

    Parameters
    ----------
    document : GeneratedDocument
        Document to render. Its text is laid out with :func:`to_html`, so every
        entity value can be read back from the PDF text.
    path : pathlib.Path
        Destination file. Parent directories are created; an existing file is
        overwritten.

    Returns
    -------
    pathlib.Path
        ``path``, once written.

    Raises
    ------
    IsADirectoryError
        If ``path`` is an existing directory.
    ImportError
        If WeasyPrint is not installed (``pip install "actadoc[generation]"``).

    Notes
    -----
    Embedded font subsets carry a timestamp. Set the ``SOURCE_DATE_EPOCH``
    environment variable (for example to ``0``) to get identical bytes for the
    same document on the same machine; ``scripts/generate_corpus.py`` does it.
    Fonts come from the system, so bytes still differ between machines.
    """
    try:
        from weasyprint import HTML
    except ImportError as error:
        raise ImportError(
            'PDF rendering needs WeasyPrint: pip install "actadoc[generation]"'
        ) from error

    path = Path(path)
    if path.is_dir():
        raise IsADirectoryError(f"{path} is a directory")
    path.parent.mkdir(parents=True, exist_ok=True)
    doc_id = document.ground_truth.doc_id
    HTML(string=to_html(document.text)).write_pdf(path, pdf_identifier=doc_id.encode())
    return path
