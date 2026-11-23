"""Command-line generation of the synthetic corpus."""

import pytest

from scripts.generate_corpus import main


def test_text_and_ground_truth_are_written(tmp_path, capsys):
    assert main(["--type", "lease", "--n", "2", "--seed", "1", "--out", str(tmp_path)]) == 0
    names = sorted(p.name for p in (tmp_path / "lease").iterdir())
    assert names == ["lease-00000.json", "lease-00000.txt", "lease-00001.json", "lease-00001.txt"]
    assert "2 lease documents written" in capsys.readouterr().out


def test_pdf_option_also_renders_pdfs(tmp_path, monkeypatch):
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    main(["--type", "energy_certificate", "--n", "1", "--out", str(tmp_path), "--pdf"])
    pdf = tmp_path / "energy_certificate" / "energy_certificate-00000.pdf"
    assert pdf.read_bytes().startswith(b"%PDF-")


def test_unknown_type_is_rejected(tmp_path):
    with pytest.raises(SystemExit):
        main(["--type", "invoice", "--out", str(tmp_path)])
