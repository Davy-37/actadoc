"""Command-line statistics of the synthetic corpus."""

from scripts.corpus_stats import main


def test_report_lists_every_type_entity_and_operation(capsys, monkeypatch):
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    assert main(["--n", "2", "--seed", "1"]) == 0
    out = capsys.readouterr().out
    assert "2 documents per type, corpus seed 1" in out
    for name in ("`lease`", "`sale_agreement`", "`energy_certificate`"):
        assert name in out
    for name in ("`cadastral_reference`", "`termination_clause`", "`stamp`", "`jpeg`"):
        assert name in out
    assert "| DPE class | A | B | C | D | E | F | G |" in out
    # tables are valid Markdown: same number of cells on every row of a table
    for table in out.split("\n\n"):
        rows = [line for line in table.splitlines() if line.startswith("|")]
        assert len({row.count("|") for row in rows}) <= 1
